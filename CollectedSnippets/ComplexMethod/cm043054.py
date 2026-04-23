async def crawl(
    request: Request,
    crawl_request: CrawlRequestWithHooks,
    _td: Dict = Depends(token_dep),
):
    """
    Crawl a list of URLs and return the results as JSON.
    For streaming responses, use /crawl/stream endpoint.
    Supports optional user-provided hook functions for customization.
    """
    if not crawl_request.urls:
        raise HTTPException(400, "At least one URL required")
    if crawl_request.hooks and not HOOKS_ENABLED:
        raise HTTPException(403, "Hooks are disabled. Set CRAWL4AI_HOOKS_ENABLED=true to enable.")
    # Check whether it is a redirection for a streaming request
    crawler_config = CrawlerRunConfig.load(crawl_request.crawler_config)
    if crawler_config.stream:
        return await stream_process(crawl_request=crawl_request)

    # Prepare hooks config if provided
    hooks_config = None
    if crawl_request.hooks:
        hooks_config = {
            'code': crawl_request.hooks.code,
            'timeout': crawl_request.hooks.timeout
        }

    results = await handle_crawl_request(
        urls=crawl_request.urls,
        browser_config=crawl_request.browser_config,
        crawler_config=crawl_request.crawler_config,
        config=config,
        hooks_config=hooks_config
    )
    # check if all of the results are not successful
    if all(not result["success"] for result in results["results"]):
        raise HTTPException(500, f"Crawl request failed: {results['results'][0]['error_message']}")
    return JSONResponse(results)