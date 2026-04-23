def _expected_large_payload_json_bytes() -> bytes:
    return json.dumps(
        LARGE_PAYLOAD,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")