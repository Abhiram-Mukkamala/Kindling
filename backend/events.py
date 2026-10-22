import uuid
from datetime import datetime
from typing import Dict, Any, Callable, Awaitable

# In-memory storage for active and completed runs
RUNS: Dict[str, Dict[str, Any]] = {}

def new_run(repo: str) -> str:
    """Initializes a new run entry and returns its unique run_id."""
    run_id = uuid.uuid4().hex[:8]
    RUNS[run_id] = {
        "repo": repo,
        "events": [],
        "done": False,
        "result": None,
    }
    return run_id

def make_emitter(run_id: str) -> Callable[[Dict[str, Any]], Awaitable[None]]:
    """Returns an asynchronous emitter function that appends sequence-stamped events."""
    async def emit(event_data: Dict[str, Any]) -> None:
        if run_id not in RUNS:
            return
        run_record = RUNS[run_id]
        events_list = run_record["events"]
        
        event = dict(event_data)
        event["run_id"] = run_id
        event["seq"] = len(events_list)
        if "started_at" not in event:
            event["started_at"] = datetime.utcnow().isoformat() + "Z"

        events_list.append(event)

    return emit
