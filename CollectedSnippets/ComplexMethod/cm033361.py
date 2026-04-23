async def webhook_trace(agent_id: str):
    def encode_webhook_id(start_ts: str) -> str:
        WEBHOOK_ID_SECRET = "webhook_id_secret"
        sig = hmac.new(
            WEBHOOK_ID_SECRET.encode("utf-8"),
            start_ts.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        return base64.urlsafe_b64encode(sig).decode("utf-8").rstrip("=")

    def decode_webhook_id(enc_id: str, webhooks: dict) -> str | None:
        for ts in webhooks.keys():
            if encode_webhook_id(ts) == enc_id:
                return ts
        return None
    since_ts = request.args.get("since_ts", type=float)
    webhook_id = request.args.get("webhook_id")

    key = f"webhook-trace-{agent_id}-logs"
    raw = REDIS_CONN.get(key)

    if since_ts is None:
        now = time.time()
        return get_json_result(
            data={
                "webhook_id": None,
                "events": [],
                "next_since_ts": now,
                "finished": False,
            }
        )

    if not raw:
        return get_json_result(
            data={
                "webhook_id": None,
                "events": [],
                "next_since_ts": since_ts,
                "finished": False,
            }
        )

    obj = json.loads(raw)
    webhooks = obj.get("webhooks", {})

    if webhook_id is None:
        candidates = [
            float(k) for k in webhooks.keys() if float(k) > since_ts
        ]

        if not candidates:
            return get_json_result(
                data={
                    "webhook_id": None,
                    "events": [],
                    "next_since_ts": since_ts,
                    "finished": False,
                }
            )

        start_ts = min(candidates)
        real_id = str(start_ts)
        webhook_id = encode_webhook_id(real_id)

        return get_json_result(
            data={
                "webhook_id": webhook_id,
                "events": [],
                "next_since_ts": start_ts,
                "finished": False,
            }
        )

    real_id = decode_webhook_id(webhook_id, webhooks)

    if not real_id:
        return get_json_result(
            data={
                "webhook_id": webhook_id,
                "events": [],
                "next_since_ts": since_ts,
                "finished": True,
            }
        )

    ws = webhooks.get(str(real_id))
    events = ws.get("events", [])
    new_events = [e for e in events if e.get("ts", 0) > since_ts]

    next_ts = since_ts
    for e in new_events:
        next_ts = max(next_ts, e["ts"])

    finished = any(e.get("event") == "finished" for e in new_events)

    return get_json_result(
        data={
            "webhook_id": webhook_id,
            "events": new_events,
            "next_since_ts": next_ts,
            "finished": finished,
        }
    )