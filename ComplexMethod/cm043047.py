async def restart_browser(req: KillBrowserRequest):
    """Restart a browser (kill + recreate). Works for permanent too.

    Args:
        sig: Browser config signature (first 8 chars), or "permanent"
    """
    try:
        from crawler_pool import (PERMANENT, HOT_POOL, COLD_POOL, LAST_USED,
                                  USAGE_COUNT, LOCK, DEFAULT_CONFIG_SIG, init_permanent)
        from crawl4ai import AsyncWebCrawler, BrowserConfig
        from contextlib import suppress
        import time

        # Handle permanent browser restart
        if req.sig == "permanent" or (DEFAULT_CONFIG_SIG and DEFAULT_CONFIG_SIG.startswith(req.sig)):
            async with LOCK:
                if PERMANENT:
                    with suppress(Exception):
                        await PERMANENT.close()

                # Reinitialize permanent
                from utils import load_config
                config = load_config()
                await init_permanent(BrowserConfig(
                    extra_args=config["crawler"]["browser"].get("extra_args", []),
                    **config["crawler"]["browser"].get("kwargs", {}),
                ))

            logger.info("🔄 Restarted permanent browser")
            return {"success": True, "restarted": "permanent"}

        # Handle hot/cold browser restart
        target_sig = None
        pool_type = None
        browser_config = None

        async with LOCK:
            # Find browser
            for sig in HOT_POOL.keys():
                if sig.startswith(req.sig):
                    target_sig = sig
                    pool_type = "hot"
                    # Would need to reconstruct config (not stored currently)
                    break

            if not target_sig:
                for sig in COLD_POOL.keys():
                    if sig.startswith(req.sig):
                        target_sig = sig
                        pool_type = "cold"
                        break

            if not target_sig:
                raise HTTPException(404, f"Browser with sig={req.sig} not found")

            # Kill existing
            if pool_type == "hot":
                browser = HOT_POOL.pop(target_sig)
            else:
                browser = COLD_POOL.pop(target_sig)

            with suppress(Exception):
                await browser.close()

            # Note: We can't easily recreate with same config without storing it
            # For now, just kill and let new requests create fresh ones
            LAST_USED.pop(target_sig, None)
            USAGE_COUNT.pop(target_sig, None)

        logger.info(f"🔄 Restarted {pool_type} browser (sig={target_sig[:8]})")

        monitor = get_monitor()
        await monitor.track_janitor_event("restart_browser", target_sig, {"pool": pool_type})

        return {"success": True, "restarted_sig": target_sig[:8], "note": "Browser will be recreated on next request"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restarting browser: {e}")
        raise HTTPException(500, str(e))