import json
import pytest
from futu_opend_mcp import skill_runner


def test_captures_json_output(capsys):
    def fake_fn(codes, output_json=False):
        print(json.dumps({"data": [{"code": c} for c in codes]}, ensure_ascii=False))
    result = skill_runner._run_skill_json(fake_fn, ["US.AAPL"])
    assert result == {"data": [{"code": "US.AAPL"}]}


def test_passes_output_json_true():
    seen = {}
    def fake_fn(code, output_json=False):
        seen["output_json"] = output_json
        print(json.dumps({"data": []}))
    skill_runner._run_skill_json(fake_fn, "HK.00700")
    assert seen["output_json"] is True


def test_systemexit_with_error_json_is_returned_as_error():
    def fake_fn(code, output_json=False):
        print(json.dumps({"error": "permission denied"}, ensure_ascii=False))
        raise SystemExit(1)
    result = skill_runner._run_skill_json(fake_fn, "HK.00700")
    assert result == {"error": "permission denied", "_skill_error": True}


def test_api_error_becomes_structured_error():
    from futu_opend_mcp import connection
    def fake_fn(code, output_json=False):
        raise connection.ApiError("snapshot failed: no permission")
    result = skill_runner._run_skill_json(fake_fn, "HK.00700")
    assert result["_skill_error"] is True
    assert "snapshot failed" in result["error"]


def test_non_json_stdout_is_wrapped_as_error():
    def fake_fn(code, output_json=False):
        print("无数据")  # not JSON
    result = skill_runner._run_skill_json(fake_fn, "HK.00700")
    assert result["_skill_error"] is True
