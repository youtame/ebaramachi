import json
import os
import time
import urllib.parse
import urllib.request

ODPT_ENDPOINT = "https://api.odpt.org/api/v4/odpt:StationTimetable"


def _json_response(status_code: int, payload: dict | list | str, is_raw_json: bool = False):
    body = payload if is_raw_json else json.dumps(payload, ensure_ascii=False)
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json; charset=utf-8"},
        "body": body,
    }


def lambda_handler(event, context):
    consumer_key = os.environ.get("ODPT_CONSUMER_KEY", "")
    if not consumer_key:
        return _json_response(500, {"error": "ODPT_CONSUMER_KEY is not configured"})

    query_params = event.get("queryStringParameters") or {}
    params = {"acl:consumerKey": consumer_key}
    allowed_keys = (
        "odpt:operator",
        "odpt:railway",
        "odpt:station",
        "odpt:calendar",
        "odpt:train",
    )
    for k in allowed_keys:
        val = query_params.get(k)
        if val:
            params[k] = val

    safe_params = {k: v for k, v in params.items() if k != "acl:consumerKey"}
    print(json.dumps({"msg": "request_odpt", "params": safe_params}, ensure_ascii=False))

    url = f"{ODPT_ENDPOINT}?{urllib.parse.urlencode(params)}"
    start_ts = time.monotonic()

    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw_body = resp.read().decode("utf-8")

        elapsed_ms = int((time.monotonic() - start_ts) * 1000)
        print(json.dumps({
            "msg": "odpt_fetched",
            "elapsed_ms": elapsed_ms,
            "bytes": len(raw_body.encode("utf-8")),
        }))

        json.loads(raw_body)
        return _json_response(200, raw_body, is_raw_json=True)

    except Exception as e:
        elapsed_ms = int((time.monotonic() - start_ts) * 1000)
        print(json.dumps({
            "msg": "odpt_error",
            "elapsed_ms": elapsed_ms,
            "error": str(e),
        }, ensure_ascii=False))
        return _json_response(502, {"error": "Failed to fetch ODPT API", "detail": str(e)})