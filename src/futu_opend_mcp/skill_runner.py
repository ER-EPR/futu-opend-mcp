"""Generic harness for calling official skill functions and capturing JSON.

Official scripts print(json.dumps(...)) and sys.exit(1) on error. We capture
stdout (never letting it reach real stdout, which would corrupt MCP stdio),
catch SystemExit, and return a dict - always a dict, never raises, so a tool
can return the dict directly as its MCP result.
"""
from __future__ import annotations

import contextlib
import io
import json
from typing import Any, Callable

from . import connection


def _run_skill_json(fn: Callable, *args: Any, **kwargs: Any) -> dict:
    buf = io.StringIO()
    err = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(err):
            fn(*args, output_json=True, **kwargs)
    except connection.ApiError as e:
        return {"_skill_error": True, "error": str(e)}
    except SystemExit:
        pass  # error JSON (if any) is in buf
    except Exception as e:  # official scripts also print+exit; some raise directly
        return {"_skill_error": True, "error": f"{type(e).__name__}: {e}"}

    raw = buf.getvalue().strip()
    if not raw:
        return {"_skill_error": True, "error": "no output from skill function"}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {"_skill_error": True, "error": f"non-JSON output: {raw[:200]}"}
    if isinstance(parsed, dict) and "error" in parsed and "_skill_error" not in parsed:
        parsed["_skill_error"] = True
    return parsed if isinstance(parsed, dict) else {"data": parsed}
