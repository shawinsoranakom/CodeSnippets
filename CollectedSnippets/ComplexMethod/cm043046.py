async def kill_browser(req: KillBrowserRequest):
    """Kill a specific browser by signature (hot or cold only).

    Args:
        sig: Browser config signature (first 8 chars)
    """
    try:
        from crawler_pool import HOT_POOL, COLD_POOL, LAST_USED, USAGE_COUNT, LOCK, DEFAULT_CONFIG_SIG
        from contextlib import suppress

        # Find full signature matching prefix
        target_sig = None
        pool_type = None

        async with LOCK:
            # Check hot pool
            for sig in HOT_POOL.keys():
                if sig.startswith(req.sig):
                    target_sig = sig
                    pool_type = "hot"
                    break

            # Check cold pool
            if not target_sig:
                for sig in COLD_POOL.keys():
                    if sig.startswith(req.sig):
                        target_sig = sig
                        pool_type = "cold"
                        break

            # Check if trying to kill permanent
            if DEFAULT_CONFIG_SIG and DEFAULT_CONFIG_SIG.startswith(req.sig):
                raise HTTPException(403, "Cannot kill permanent browser. Use restart instead.")

            if not target_sig:
                raise HTTPException(404, f"Browser with sig={req.sig} not found")

            # Warn if there are active requests (browser might be in use)
            monitor = get_monitor()
            active_count = len(monitor.get_active_requests())
            if active_count > 0:
                logger.warning(f"Killing browser {target_sig[:8]} while {active_count} requests are active - may cause failures")

            # Kill the browser
            if pool_type == "hot":
                browser = HOT_POOL.pop(target_sig)
            else:
                browser = COLD_POOL.pop(target_sig)

            with suppress(Exception):
                await browser.close()

            LAST_USED.pop(target_sig, None)
            USAGE_COUNT.pop(target_sig, None)

        logger.info(f"🔪 Killed {pool_type} browser (sig={target_sig[:8]})")

        monitor = get_monitor()
        await monitor.track_janitor_event("kill_browser", target_sig, {"pool": pool_type, "manual": True})

        return {"success": True, "killed_sig": target_sig[:8], "pool_type": pool_type}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error killing browser: {e}")
        raise HTTPException(500, str(e))