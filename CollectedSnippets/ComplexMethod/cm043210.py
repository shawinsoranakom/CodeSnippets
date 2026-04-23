async def arun(
        self,
        url: str,
        config: CrawlerRunConfig = None,
        **kwargs,
    ) -> RunManyReturn:
        """
        Runs the crawler for a single source: URL (web, local file, or raw HTML).

        Migration Guide:
        Old way (deprecated):
            result = await crawler.arun(
                url="https://example.com",
                word_count_threshold=200,
                screenshot=True,
                ...
            )

        New way (recommended):
            config = CrawlerRunConfig(
                word_count_threshold=200,
                screenshot=True,
                ...
            )
            result = await crawler.arun(url="https://example.com", config=config)

        Args:
            url: The URL to crawl (http://, https://, file://, or raw:)
            config: Configuration object controlling crawl behavior
            [other parameters maintained for backwards compatibility]

        Returns:
            CrawlResult: The result of crawling and processing
        """
        # Auto-start if not ready
        if not self.ready:
            await self.start()

        config = config or CrawlerRunConfig()
        if not isinstance(url, str) or not url:
            raise ValueError(
                "Invalid URL, make sure the URL is a non-empty string")

        async with self._lock or self.nullcontext():
            try:
                self.logger.verbose = config.verbose

                # Default to ENABLED if no cache mode specified
                if config.cache_mode is None:
                    config.cache_mode = CacheMode.ENABLED

                # Create cache context
                cache_context = CacheContext(url, config.cache_mode, False)

                # Initialize processing variables
                async_response: AsyncCrawlResponse = None
                cached_result: CrawlResult = None
                screenshot_data = None
                pdf_data = None
                extracted_content = None
                start_time = time.perf_counter()

                # Try to get cached result if appropriate
                if cache_context.should_read():
                    cached_result = await async_db_manager.aget_cached_url(url)

                # Smart Cache: Validate cache freshness if enabled
                if cached_result and config.check_cache_freshness:
                    cache_metadata = await async_db_manager.aget_cache_metadata(url)
                    if cache_metadata:
                        async with CacheValidator(timeout=config.cache_validation_timeout) as validator:
                            validation = await validator.validate(
                                url=url,
                                stored_etag=cache_metadata.get("etag"),
                                stored_last_modified=cache_metadata.get("last_modified"),
                                stored_head_fingerprint=cache_metadata.get("head_fingerprint"),
                            )

                        if validation.status == CacheValidationResult.FRESH:
                            cached_result.cache_status = "hit_validated"
                            self.logger.info(
                                message="Cache validated: {reason}",
                                tag="CACHE",
                                params={"reason": validation.reason}
                            )
                            # Update metadata if we got new values
                            if validation.new_etag or validation.new_last_modified:
                                await async_db_manager.aupdate_cache_metadata(
                                    url=url,
                                    etag=validation.new_etag,
                                    last_modified=validation.new_last_modified,
                                    head_fingerprint=validation.new_head_fingerprint,
                                )
                        elif validation.status == CacheValidationResult.ERROR:
                            cached_result.cache_status = "hit_fallback"
                            self.logger.warning(
                                message="Cache validation failed, using cached: {reason}",
                                tag="CACHE",
                                params={"reason": validation.reason}
                            )
                        else:
                            # STALE or UNKNOWN - force recrawl
                            self.logger.info(
                                message="Cache stale: {reason}",
                                tag="CACHE",
                                params={"reason": validation.reason}
                            )
                            cached_result = None
                elif cached_result:
                    cached_result.cache_status = "hit"

                if cached_result:
                    html = sanitize_input_encode(cached_result.html)
                    extracted_content = sanitize_input_encode(
                        cached_result.extracted_content or ""
                    )
                    extracted_content = (
                        None
                        if not extracted_content or extracted_content == "[]"
                        else extracted_content
                    )
                    # If screenshot is requested but its not in cache, then set cache_result to None
                    screenshot_data = cached_result.screenshot
                    pdf_data = cached_result.pdf
                    # if config.screenshot and not screenshot or config.pdf and not pdf:
                    if config.screenshot and not screenshot_data:
                        cached_result = None

                    if config.pdf and not pdf_data:
                        cached_result = None

                    self.logger.url_status(
                        url=cache_context.display_url,
                        success=bool(html),
                        timing=time.perf_counter() - start_time,
                        tag="FETCH",
                    )

                # Update proxy configuration from rotation strategy if available
                if config and config.proxy_rotation_strategy:
                    # Handle sticky sessions - use same proxy for all requests with same session_id
                    if config.proxy_session_id:
                        next_proxy: ProxyConfig = await config.proxy_rotation_strategy.get_proxy_for_session(
                            config.proxy_session_id,
                            ttl=config.proxy_session_ttl
                        )
                        if next_proxy:
                            self.logger.info(
                                message="Using sticky proxy session: {session_id} -> {proxy}",
                                tag="PROXY",
                                params={
                                    "session_id": config.proxy_session_id,
                                    "proxy": next_proxy.server
                                }
                            )
                            config.proxy_config = next_proxy
                    else:
                        # Existing behavior: rotate on each request
                        next_proxy: ProxyConfig = await config.proxy_rotation_strategy.get_next_proxy()
                        if next_proxy:
                            self.logger.info(
                                message="Switch proxy: {proxy}",
                                tag="PROXY",
                                params={"proxy": next_proxy.server}
                            )
                            config.proxy_config = next_proxy

                # Fetch fresh content if needed
                if not cached_result or not html:
                    from urllib.parse import urlparse

                    # Check robots.txt if enabled (once, before any attempts)
                    if config and config.check_robots_txt:
                        if not await self.robots_parser.can_fetch(
                            url, self.browser_config.user_agent
                        ):
                            return CrawlResult(
                                url=url,
                                html="",
                                success=False,
                                status_code=403,
                                error_message="Access denied by robots.txt",
                                response_headers={
                                    "X-Robots-Status": "Blocked by robots.txt"
                                },
                            )

                    # --- Anti-bot retry setup ---
                    # raw: URLs contain caller-provided HTML (e.g. from cache),
                    # not content fetched from a web server.  Anti-bot detection,
                    # proxy retries, and fallback fetching are meaningless here.
                    _is_raw_url = url.startswith("raw:") or url.startswith("raw://")

                    _max_attempts = 1 + getattr(config, "max_retries", 0)
                    _proxy_list = config._get_proxy_list()
                    _original_proxy_config = config.proxy_config
                    _block_reason = ""
                    _done = False
                    crawl_result = None
                    _crawl_stats = {
                        "attempts": 0,
                        "retries": 0,
                        "proxies_used": [],
                        "fallback_fetch_used": False,
                        "resolved_by": None,
                    }

                    for _attempt in range(_max_attempts):
                        if _done:
                            break

                        if _attempt > 0:
                            _crawl_stats["retries"] = _attempt
                            self.logger.warning(
                                message="Anti-bot retry {attempt}/{max_retries} for {url} — {reason}",
                                tag="ANTIBOT",
                                params={
                                    "attempt": _attempt,
                                    "max_retries": config.max_retries,
                                    "url": url[:80],
                                    "reason": _block_reason,
                                },
                            )

                        for _p_idx, _proxy in enumerate(_proxy_list):
                            if _p_idx > 0 or _attempt > 0:
                                self.logger.info(
                                    message="Trying proxy {idx}/{total}: {proxy}",
                                    tag="ANTIBOT",
                                    params={
                                        "idx": _p_idx + 1,
                                        "total": len(_proxy_list),
                                        "proxy": _proxy.server if _proxy else "direct",
                                    },
                                )

                            # Set the active proxy for this attempt
                            config.proxy_config = _proxy
                            _crawl_stats["attempts"] += 1

                            try:
                                t1 = time.perf_counter()

                                if config.user_agent:
                                    self.crawler_strategy.update_user_agent(
                                        config.user_agent)

                                async_response = await self.crawler_strategy.crawl(
                                    url, config=config)

                                html = sanitize_input_encode(async_response.html)
                                screenshot_data = async_response.screenshot
                                pdf_data = async_response.pdf_data
                                js_execution_result = async_response.js_execution_result

                                self.logger.url_status(
                                    url=cache_context.display_url,
                                    success=bool(html),
                                    timing=time.perf_counter() - t1,
                                    tag="FETCH",
                                )

                                crawl_result = await self.aprocess_html(
                                    url=url, html=html,
                                    extracted_content=extracted_content,
                                    config=config,
                                    screenshot_data=screenshot_data,
                                    pdf_data=pdf_data,
                                    verbose=config.verbose,
                                    is_raw_html=True if url.startswith("raw:") else False,
                                    redirected_url=async_response.redirected_url,
                                    original_scheme=urlparse(url).scheme,
                                    **kwargs,
                                )

                                crawl_result.status_code = async_response.status_code
                                is_raw_url = url.startswith("raw:") or url.startswith("raw://")
                                crawl_result.redirected_url = async_response.redirected_url or (None if is_raw_url else url)
                                crawl_result.redirected_status_code = async_response.redirected_status_code
                                crawl_result.response_headers = async_response.response_headers
                                crawl_result.downloaded_files = async_response.downloaded_files
                                crawl_result.js_execution_result = js_execution_result
                                crawl_result.mhtml = async_response.mhtml_data
                                crawl_result.ssl_certificate = async_response.ssl_certificate
                                crawl_result.network_requests = async_response.network_requests
                                crawl_result.console_messages = async_response.console_messages
                                crawl_result.success = bool(html)
                                crawl_result.session_id = getattr(config, "session_id", None)
                                crawl_result.cache_status = "miss"

                                # Check if blocked (skip for raw: URLs —
                                # caller-provided content, anti-bot N/A)
                                if _is_raw_url:
                                    _blocked = False
                                    _block_reason = ""
                                else:
                                    _blocked, _block_reason = is_blocked(
                                        async_response.status_code, html)

                                _crawl_stats["proxies_used"].append({
                                    "proxy": _proxy.server if _proxy else None,
                                    "status_code": async_response.status_code,
                                    "blocked": _blocked,
                                    "reason": _block_reason if _blocked else "",
                                })

                                if not _blocked:
                                    _crawl_stats["resolved_by"] = "proxy" if _proxy else "direct"
                                    _done = True
                                    break  # Success — exit proxy loop

                            except Exception as _crawl_err:
                                _crawl_stats["proxies_used"].append({
                                    "proxy": _proxy.server if _proxy else None,
                                    "status_code": None,
                                    "blocked": True,
                                    "reason": str(_crawl_err),
                                })
                                self.logger.error_status(
                                    url=url,
                                    error=f"Proxy {_proxy.server if _proxy else 'direct'} failed: {_crawl_err}",
                                    tag="ANTIBOT",
                                )
                                _block_reason = str(_crawl_err)
                                # If this is the only proxy and only attempt, re-raise
                                # so the caller gets the real error (not a silent swallow).
                                # But if there are more proxies or retries to try, continue.
                                if len(_proxy_list) <= 1 and _max_attempts <= 1:
                                    raise

                    # Restore original proxy_config
                    config.proxy_config = _original_proxy_config

                    # --- Fallback fetch function (last resort after all retries+proxies exhausted) ---
                    # Invoke fallback when: (a) crawl_result exists but is blocked, OR
                    # (b) crawl_result is None because all proxies threw exceptions (browser crash, timeout).
                    # Skip for raw: URLs — fallback expects a real URL, not raw HTML content.
                    _fallback_fn = getattr(config, "fallback_fetch_function", None)
                    if _fallback_fn and not _done and not _is_raw_url:
                        _needs_fallback = (
                            crawl_result is None  # All proxies threw exceptions
                            or is_blocked(crawl_result.status_code, crawl_result.html or "")[0]
                        )
                        if _needs_fallback:
                            self.logger.warning(
                                message="All retries exhausted, invoking fallback_fetch_function for {url}",
                                tag="ANTIBOT",
                                params={"url": url[:80]},
                            )
                            _crawl_stats["fallback_fetch_used"] = True
                            try:
                                _fallback_html = await _fallback_fn(url)
                                if _fallback_html:
                                    _sanitized_html = sanitize_input_encode(_fallback_html)
                                    try:
                                        crawl_result = await self.aprocess_html(
                                            url=url,
                                            html=_sanitized_html,
                                            extracted_content=extracted_content,
                                            config=config,
                                            screenshot_data=None,
                                            pdf_data=None,
                                            verbose=config.verbose,
                                            is_raw_html=True,
                                            redirected_url=url,
                                            original_scheme=urlparse(url).scheme,
                                            **kwargs,
                                        )
                                    except Exception as _proc_err:
                                        # aprocess_html may fail if browser is dead (e.g.,
                                        # consent popup removal needs Page.evaluate).
                                        # Fall back to a minimal result with raw HTML.
                                        self.logger.warning(
                                            message="Fallback HTML processing failed ({err}), using raw HTML",
                                            tag="ANTIBOT",
                                            params={"err": str(_proc_err)[:100]},
                                        )
                                        crawl_result = CrawlResult(
                                            url=url,
                                            html=_sanitized_html,
                                            success=True,
                                            status_code=200,
                                        )
                                    crawl_result.success = True
                                    crawl_result.status_code = 200
                                    crawl_result.session_id = getattr(config, "session_id", None)
                                    crawl_result.cache_status = "miss"
                                    _crawl_stats["resolved_by"] = "fallback_fetch"
                            except Exception as _fallback_err:
                                self.logger.error_status(
                                    url=url,
                                    error=f"Fallback fetch failed: {_fallback_err}",
                                    tag="ANTIBOT",
                                )

                    # --- Mark blocked results as failed ---
                    # Skip re-check ONLY when fallback SUCCEEDED — the fallback result
                    # is authoritative and real pages may contain anti-bot script markers
                    # (e.g. PerimeterX JS on Walmart) that trigger false positives.
                    # When fallback was attempted but FAILED, we must still re-check
                    # because the result is from a blocked proxy attempt.
                    # Also skip for raw: URLs — caller-provided content, anti-bot N/A.
                    if crawl_result:
                        _fallback_succeeded = _crawl_stats.get("resolved_by") == "fallback_fetch"
                        if not _fallback_succeeded and not _is_raw_url:
                            _blocked, _block_reason = is_blocked(
                                crawl_result.status_code, crawl_result.html or "")
                            if _blocked:
                                crawl_result.success = False
                                crawl_result.error_message = f"Blocked by anti-bot protection: {_block_reason}"
                        crawl_result.crawl_stats = _crawl_stats
                    else:
                        # All proxies threw exceptions and fallback either wasn't
                        # configured or also failed.  Build a minimal result so the
                        # caller gets crawl_stats instead of None.
                        crawl_result = CrawlResult(
                            url=url,
                            html="",
                            success=False,
                            status_code=None,
                            error_message=f"All proxies failed: {_block_reason}" if _block_reason else "All proxies failed",
                        )
                        crawl_result.crawl_stats = _crawl_stats

                    # Compute head fingerprint for cache validation
                    if crawl_result and crawl_result.html:
                        head_end = crawl_result.html.lower().find('</head>')
                        if head_end != -1:
                            head_html = crawl_result.html[:head_end + 7]
                            crawl_result.head_fingerprint = compute_head_fingerprint(head_html)

                    self.logger.url_status(
                        url=cache_context.display_url,
                        success=crawl_result.success if crawl_result else False,
                        timing=time.perf_counter() - start_time,
                        tag="COMPLETE",
                    )

                    # Update cache if appropriate
                    if cache_context.should_write() and not bool(cached_result):
                        await async_db_manager.acache_url(crawl_result)

                    return CrawlResultContainer(crawl_result)

                else:
                    self.logger.url_status(
                        url=cache_context.display_url,
                        success=True,
                        timing=time.perf_counter() - start_time,
                        tag="COMPLETE"
                    )
                    cached_result.success = bool(html)
                    cached_result.session_id = getattr(
                        config, "session_id", None)
                    # For raw: URLs, don't fall back to the raw HTML string as redirected_url
                    is_raw_url = url.startswith("raw:") or url.startswith("raw://")
                    cached_result.redirected_url = cached_result.redirected_url or (None if is_raw_url else url)
                    return CrawlResultContainer(cached_result)

            except Exception as e:
                error_context = get_error_context(sys.exc_info())

                error_message = (
                    f"Unexpected error in _crawl_web at line {error_context['line_no']} "
                    f"in {error_context['function']} ({error_context['filename']}):\n"
                    f"Error: {str(e)}\n\n"
                    f"Code context:\n{error_context['code_context']}"
                )

                self.logger.error_status(
                    url=url,
                    error=error_message,
                    tag="ERROR",
                )

                return CrawlResultContainer(
                    CrawlResult(
                        url=url, html="", success=False, error_message=error_message
                    )
                )