def run(
        self,
        url: str,
        word_count_threshold=MIN_WORD_THRESHOLD,
        extraction_strategy: ExtractionStrategy = None,
        chunking_strategy: ChunkingStrategy = RegexChunking(),
        bypass_cache: bool = False,
        css_selector: str = None,
        screenshot: bool = False,
        user_agent: str = None,
        verbose=True,
        **kwargs,
    ) -> CrawlResult:
        try:
            extraction_strategy = extraction_strategy or NoExtractionStrategy()
            extraction_strategy.verbose = verbose
            if not isinstance(extraction_strategy, ExtractionStrategy):
                raise ValueError("Unsupported extraction strategy")
            if not isinstance(chunking_strategy, ChunkingStrategy):
                raise ValueError("Unsupported chunking strategy")

            word_count_threshold = max(word_count_threshold, MIN_WORD_THRESHOLD)

            cached = None
            screenshot_data = None
            extracted_content = None
            if not bypass_cache and not self.always_by_pass_cache:
                cached = get_cached_url(url)

            if kwargs.get("warmup", True) and not self.ready:
                return None

            if cached:
                html = sanitize_input_encode(cached[1])
                extracted_content = sanitize_input_encode(cached[4])
                if screenshot:
                    screenshot_data = cached[9]
                    if not screenshot_data:
                        cached = None

            if not cached or not html:
                if user_agent:
                    self.crawler_strategy.update_user_agent(user_agent)
                t1 = time.time()
                html = sanitize_input_encode(self.crawler_strategy.crawl(url, **kwargs))
                t2 = time.time()
                if verbose:
                    print(
                        f"[LOG] 🚀 Crawling done for {url}, success: {bool(html)}, time taken: {t2 - t1:.2f} seconds"
                    )
                if screenshot:
                    screenshot_data = self.crawler_strategy.take_screenshot()

            crawl_result = self.process_html(
                url,
                html,
                extracted_content,
                word_count_threshold,
                extraction_strategy,
                chunking_strategy,
                css_selector,
                screenshot_data,
                verbose,
                bool(cached),
                **kwargs,
            )
            crawl_result.success = bool(html)
            return crawl_result
        except Exception as e:
            if not hasattr(e, "msg"):
                e.msg = str(e)
            print(f"[ERROR] 🚫 Failed to crawl {url}, error: {e.msg}")
            return CrawlResult(url=url, html="", success=False, error_message=e.msg)