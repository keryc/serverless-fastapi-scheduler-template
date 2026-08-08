"""
Cross-checks between serverless.yml, events/*.yml, the task registry and the
Makefile. These catch wiring mistakes (a TASK_ID with no task, a schedule file
nobody references, a Makefile mapping gone stale) at test time instead of at
deploy time.
"""

import re
from pathlib import Path

import pytest
import yaml

from src.tasks.registry import TaskRegistry

ROOT = Path(__file__).resolve().parents[2]
SERVERLESS_YML = ROOT / "serverless.yml"
EVENTS_DIR = ROOT / "events"
MAKEFILE = ROOT / "Makefile"

TASK_HANDLER = "src/handlers/task_handlers.task_handler"


class _CfnLoader(yaml.SafeLoader):
    """SafeLoader that tolerates CloudFormation tags (!Sub, !GetAtt, !Ref)."""


_CfnLoader.add_multi_constructor("!", lambda loader, suffix, node: None)


def load_serverless() -> dict:
    return yaml.load(SERVERLESS_YML.read_text(), Loader=_CfnLoader)


@pytest.fixture(scope="module")
def config() -> dict:
    return load_serverless()


@pytest.fixture(scope="module")
def task_functions(config) -> dict[str, dict]:
    """Functions that use the shared task handler, by function name."""
    return {
        name: fn for name, fn in config["functions"].items() if fn.get("handler") == TASK_HANDLER
    }


def test_serverless_yml_parses(config):
    assert config["service"]
    assert config["functions"]


def test_task_functions_exist(task_functions):
    assert task_functions, f"no function uses {TASK_HANDLER}"


def test_every_task_id_is_registered(task_functions):
    for name, fn in task_functions.items():
        task_id = fn.get("environment", {}).get("TASK_ID")
        assert task_id, f"function '{name}' has no TASK_ID"
        assert TaskRegistry.exists(task_id), (
            f"function '{name}' points at unknown task '{task_id}'. "
            f"Registered: {TaskRegistry.all_ids()}"
        )


def test_every_registered_task_has_a_function(task_functions):
    wired = {fn.get("environment", {}).get("TASK_ID") for fn in task_functions.values()}
    orphans = set(TaskRegistry.all_ids()) - wired
    assert not orphans, f"tasks with no Lambda function in serverless.yml: {sorted(orphans)}"


def test_event_files_referenced_by_functions_exist(task_functions):
    for name, fn in task_functions.items():
        events = fn.get("events")
        assert isinstance(events, str), f"function '{name}' should reference an events file"
        match = re.fullmatch(r"\$\{file\(\./(events/.+\.yml)\):events\}", events)
        assert match, f"function '{name}' has an unexpected events reference: {events}"
        assert (ROOT / match.group(1)).exists(), f"missing {match.group(1)}"


def test_no_orphan_event_files(task_functions):
    referenced = {
        re.fullmatch(r"\$\{file\(\./(events/.+\.yml)\):events\}", fn["events"]).group(1)
        for fn in task_functions.values()
    }
    on_disk = {f"events/{p.name}" for p in EVENTS_DIR.glob("*.yml")}
    assert on_disk == referenced, (
        f"events/ files nobody references: {sorted(on_disk - referenced)}; "
        f"referenced but missing: {sorted(referenced - on_disk)}"
    )


@pytest.mark.parametrize("path", sorted(EVENTS_DIR.glob("*.yml")), ids=lambda p: p.name)
def test_event_file_schedules_are_well_formed(path):
    doc = yaml.safe_load(path.read_text())
    events = doc["events"]
    assert events, f"{path.name} declares no events"

    for entry in events:
        schedule = entry["schedule"]
        rate = schedule["rate"]
        assert re.fullmatch(r"(rate|cron)\(.+\)", rate), f"bad rate in {path.name}: {rate}"
        assert "enabled" in schedule, f"{path.name}: schedule missing 'enabled'"
        # `input` is optional, but when present it must be a mapping: it becomes
        # TaskConfig.params. Without it the task receives the whole EventBridge
        # envelope instead.
        if "input" in schedule:
            assert isinstance(schedule["input"], dict)


def test_api_stays_within_the_api_gateway_limit(config):
    """The api function inherits provider.timeout, which resolves per stage."""
    api_override = config["functions"]["api"].get("timeout")
    if api_override is not None:
        assert api_override <= 29, "API Gateway caps integrations at 29s"

    for stage, values in config["custom"]["stages"].items():
        assert values["timeout"] <= 29, f"stage '{stage}': API Gateway caps integrations at 29s"


def test_scheduled_tasks_can_outlive_the_api_timeout(config):
    for stage, values in config["custom"]["stages"].items():
        assert (
            values["taskTimeout"] >= values["timeout"]
        ), f"stage '{stage}': taskTimeout should not be shorter than the API timeout"
        assert values["taskTimeout"] <= 900, f"stage '{stage}': Lambda caps timeout at 900s"


def test_makefile_task_map_matches_serverless(task_functions):
    """The Makefile's TASK_MAP drives `make invoke`/`make logs`."""
    line = re.search(r"^TASK_MAP := (.+)$", MAKEFILE.read_text(), re.M)
    assert line, "TASK_MAP not found in the Makefile"

    mapping = dict(entry.split(":") for entry in line.group(1).split())
    expected = {fn["environment"]["TASK_ID"]: name for name, fn in task_functions.items()}
    assert mapping == expected, (
        "Makefile TASK_MAP is out of sync with serverless.yml. "
        f"Expected {expected}, got {mapping}"
    )
