async def arun_many(
        self,
        urls: List[str],
        config: Optional[Union[CrawlerRunConfig, List[CrawlerRunConfig]]] = None,
        dispatcher: Optional[BaseDispatcher] = None,
        # Legacy parameters maintained for backwards compatibility
        # word_count_threshold=MIN_WORD_THRESHOLD,
        # extraction_strategy: ExtractionStrategy = None,
        # chunking_strategy: ChunkingStrategy = RegexChunking(),
        # content_filter: RelevantContentFilter = None,
        # cache_mode: Optional[CacheMode] = None,
        # bypass_cache: bool = False,
        # css_selector: str = None,
        # screenshot: bool = False,
        # pdf: bool = False,
        # user_agent: str = None,
        # verbose=True,
        **kwargs,
    ) -> RunManyReturn:
        """
        Runs the crawler for multiple URLs concurrently using a configurable dispatcher strategy.

        Args:
        urls: List of URLs to crawl
        config: Configuration object(s) controlling crawl behavior. Can be:
            - Single CrawlerRunConfig: Used for all URLs
            - List[CrawlerRunConfig]: Configs with url_matcher for URL-specific settings
        dispatcher: The dispatcher strategy instance to use. Defaults to MemoryAdaptiveDispatcher
        [other parameters maintained for backwards compatibility]

        Returns:
        Union[List[CrawlResult], AsyncGenerator[CrawlResult, None]]:
            Either a list of all results or an async generator yielding results

        Examples:

        # Batch processing (default)
        results = await crawler.arun_many(
            urls=["https://example1.com", "https://example2.com"],
            config=CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
        )
        for result in results:
            print(f"Processed {result.url}: {len(result.markdown)} chars")

        # Streaming results
        async for result in await crawler.arun_many(
            urls=["https://example1.com", "https://example2.com"],
            config=CrawlerRunConfig(cache_mode=CacheMode.BYPASS, stream=True),
        ):
            print(f"Processed {result.url}: {len(result.markdown)} chars")
        """
        config = config or CrawlerRunConfig()

        # When deep_crawl_strategy is set, bypass the dispatcher and call
        # arun() directly for each URL.  The DeepCrawlDecorator on arun()
        # will invoke the strategy and return List[CrawlResult].  The
        # dispatcher cannot handle that return type (it expects a single
        # CrawlResult), so we must handle it here.
        primary_cfg = config[0] if isinstance(config, list) else config
        if getattr(primary_cfg, "deep_crawl_strategy", None):
            if primary_cfg.stream:
                async def _deep_crawl_stream():
                    for url in urls:
                        result = await self.arun(url, config=primary_cfg)
                        if isinstance(result, list):
                            for r in result:
                                yield r
                        else:
                            async for r in result:
                                yield r
                return _deep_crawl_stream()
            else:
                all_results = []
                for url in urls:
                    result = await self.arun(url, config=primary_cfg)
                    if isinstance(result, list):
                        all_results.extend(result)
                    else:
                        all_results.append(result)
                return all_results

        if dispatcher is None:
            primary_cfg = config[0] if isinstance(config, list) else config
            mean_delay = getattr(primary_cfg, "mean_delay", 0.1)
            max_range = getattr(primary_cfg, "max_range", 0.3)
            dispatcher = MemoryAdaptiveDispatcher(
                rate_limiter=RateLimiter(
                    base_delay=(mean_delay, mean_delay + max_range),
                    max_delay=60.0,
                    max_retries=3,
                ),
            )

        def transform_result(task_result):
            return (
                setattr(
                    task_result.result,
                    "dispatch_result",
                    DispatchResult(
                        task_id=task_result.task_id,
                        memory_usage=task_result.memory_usage,
                        peak_memory=task_result.peak_memory,
                        start_time=task_result.start_time,
                        end_time=task_result.end_time,
                        error_message=task_result.error_message,
                    ),
                )
                or task_result.result
            )

        # Handle stream setting - use first config's stream setting if config is a list
        if isinstance(config, list):
            stream = config[0].stream if config else False
            primary_config = config[0] if config else None
        else:
            stream = config.stream
            primary_config = config

        # Helper to release sticky session if auto_release is enabled
        async def maybe_release_session():
            if (primary_config and
                primary_config.proxy_session_id and
                primary_config.proxy_session_auto_release and
                primary_config.proxy_rotation_strategy):
                await primary_config.proxy_rotation_strategy.release_session(
                    primary_config.proxy_session_id
                )
                self.logger.info(
                    message="Auto-released proxy session: {session_id}",
                    tag="PROXY",
                    params={"session_id": primary_config.proxy_session_id}
                )

        if stream:
            async def result_transformer():
                try:
                    async for task_result in dispatcher.run_urls_stream(
                        crawler=self, urls=urls, config=config
                    ):
                        yield transform_result(task_result)
                finally:
                    # Auto-release session after streaming completes
                    await maybe_release_session()

            return result_transformer()
        else:
            try:
                _results = await dispatcher.run_urls(crawler=self, urls=urls, config=config)
                return [transform_result(res) for res in _results]
            finally:
                # Auto-release session after batch completes
                await maybe_release_session()