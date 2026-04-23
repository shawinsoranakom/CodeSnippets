async def handle_stream_crawl_request(
    urls: List[str],
    browser_config: dict,
    crawler_config: dict,
    config: dict,
    hooks_config: Optional[dict] = None
) -> Tuple[AsyncWebCrawler, AsyncGenerator, Optional[Dict]]:
    """Handle streaming crawl requests with optional hooks."""
    hooks_info = None
    crawler = None
    try:
        browser_config = BrowserConfig.load(browser_config)
        # browser_config.verbose = True # Set to False or remove for production stress testing
        browser_config.verbose = False
        crawler_config = CrawlerRunConfig.load(crawler_config)
        crawler_config.scraping_strategy = LXMLWebScrapingStrategy()
        crawler_config.stream = True

        # Deep crawl streaming supports exactly one start URL
        if crawler_config.deep_crawl_strategy is not None and len(urls) != 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Deep crawling with stream currently supports exactly one URL per request. "
                    f"Received {len(urls)} URLs."
                ),
            )

        from crawler_pool import get_crawler, release_crawler
        crawler = await get_crawler(browser_config)

        # Attach hooks if provided
        if hooks_config:
            from hook_manager import attach_user_hooks_to_crawler, UserHookManager
            hook_manager = UserHookManager(timeout=hooks_config.get('timeout', 30))
            hooks_status, hook_manager = await attach_user_hooks_to_crawler(
                crawler,
                hooks_config.get('code', {}),
                timeout=hooks_config.get('timeout', 30),
                hook_manager=hook_manager
            )
            logger.info(f"Hooks attachment status for streaming: {hooks_status['status']}")
            # Include hook manager in hooks_info for proper tracking
            hooks_info = {'status': hooks_status, 'manager': hook_manager}

        # Deep crawl with single URL: use arun() which returns an async generator
        # mirroring the Python library's streaming behavior
        if crawler_config.deep_crawl_strategy is not None and len(urls) == 1:
            results_gen = await crawler.arun(
                urls[0],
                config=crawler_config,
            )
        else:
            # Default multi-URL streaming via arun_many
            dispatcher = MemoryAdaptiveDispatcher(
                memory_threshold_percent=config["crawler"]["memory_threshold_percent"],
                rate_limiter=RateLimiter(
                    base_delay=tuple(config["crawler"]["rate_limiter"]["base_delay"])
                )
            )
            results_gen = await crawler.arun_many(
                urls=urls,
                config=crawler_config,
                dispatcher=dispatcher
            )

        return crawler, results_gen, hooks_info

    except Exception as e:
        # Release crawler on setup error (for successful streams,
        # release happens in stream_results finally block)
        if crawler:
            await release_crawler(crawler)
        logger.error(f"Stream crawl error: {str(e)}", exc_info=True)
        # Raising HTTPException here will prevent streaming response
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )