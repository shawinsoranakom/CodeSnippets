async def get_crawler(cfg: BrowserConfig) -> AsyncWebCrawler:
    """Get crawler from pool with tiered strategy."""
    sig = _sig(cfg)
    async with LOCK:
        # Check permanent browser for default config
        if PERMANENT and _is_default_config(sig):
            LAST_USED[sig] = time.time()
            USAGE_COUNT[sig] = USAGE_COUNT.get(sig, 0) + 1
            if not hasattr(PERMANENT, 'active_requests'):
                PERMANENT.active_requests = 0
            PERMANENT.active_requests += 1
            logger.info("🔥 Using permanent browser")
            return PERMANENT

        # Check hot pool
        if sig in HOT_POOL:
            LAST_USED[sig] = time.time()
            USAGE_COUNT[sig] = USAGE_COUNT.get(sig, 0) + 1
            crawler = HOT_POOL[sig]
            if not hasattr(crawler, 'active_requests'):
                crawler.active_requests = 0
            crawler.active_requests += 1
            logger.info(f"♨️  Using hot pool browser (sig={sig[:8]}, active={crawler.active_requests})")
            return crawler

        # Check cold pool (promote to hot if used 3+ times)
        if sig in COLD_POOL:
            LAST_USED[sig] = time.time()
            USAGE_COUNT[sig] = USAGE_COUNT.get(sig, 0) + 1
            crawler = COLD_POOL[sig]
            if not hasattr(crawler, 'active_requests'):
                crawler.active_requests = 0
            crawler.active_requests += 1

            if USAGE_COUNT[sig] >= 3:
                logger.info(f"⬆️  Promoting to hot pool (sig={sig[:8]}, count={USAGE_COUNT[sig]})")
                HOT_POOL[sig] = COLD_POOL.pop(sig)

                # Track promotion in monitor
                try:
                    from monitor import get_monitor
                    await get_monitor().track_janitor_event("promote", sig, {"count": USAGE_COUNT[sig]})
                except:
                    pass

                return HOT_POOL[sig]

            logger.info(f"❄️  Using cold pool browser (sig={sig[:8]})")
            return crawler

        # Memory check before creating new
        mem_pct = get_container_memory_percent()
        if mem_pct >= MEM_LIMIT:
            logger.error(f"💥 Memory pressure: {mem_pct:.1f}% >= {MEM_LIMIT}%")
            raise MemoryError(f"Memory at {mem_pct:.1f}%, refusing new browser")

        # Create new in cold pool
        logger.info(f"🆕 Creating new browser in cold pool (sig={sig[:8]}, mem={mem_pct:.1f}%)")
        crawler = AsyncWebCrawler(config=cfg, thread_safe=False)
        await crawler.start()
        crawler.active_requests = 1
        COLD_POOL[sig] = crawler
        LAST_USED[sig] = time.time()
        USAGE_COUNT[sig] = 1
        return crawler