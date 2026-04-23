async def seed_assets(request: web.Request) -> web.Response:
    """Trigger asset seeding for specified roots (models, input, output).

    Query params:
        wait: If "true", block until scan completes (synchronous behavior for tests)

    Returns:
        202 Accepted if scan started
        409 Conflict if scan already running
        200 OK with final stats if wait=true
    """
    try:
        payload = await request.json()
        roots = payload.get("roots", ["models", "input", "output"])
    except Exception:
        roots = ["models", "input", "output"]

    valid_roots = tuple(r for r in roots if r in ("models", "input", "output"))
    if not valid_roots:
        return _build_error_response(400, "INVALID_BODY", "No valid roots specified")

    wait_param = request.query.get("wait", "").lower()
    should_wait = wait_param in ("true", "1", "yes")

    started = asset_seeder.start(roots=valid_roots)
    if not started:
        return web.json_response({"status": "already_running"}, status=409)

    if should_wait:
        await asyncio.to_thread(asset_seeder.wait)
        status = asset_seeder.get_status()
        return web.json_response(
            {
                "status": "completed",
                "progress": {
                    "scanned": status.progress.scanned if status.progress else 0,
                    "total": status.progress.total if status.progress else 0,
                    "created": status.progress.created if status.progress else 0,
                    "skipped": status.progress.skipped if status.progress else 0,
                },
                "errors": status.errors,
            },
            status=200,
        )

    return web.json_response({"status": "started"}, status=202)