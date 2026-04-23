async def handle_markdown_request(
    url: str,
    filter_type: FilterType,
    query: Optional[str] = None,
    cache: str = "0",
    config: Optional[dict] = None,
    provider: Optional[str] = None,
    temperature: Optional[float] = None,
    base_url: Optional[str] = None
) -> str:
    """Handle markdown generation requests."""
    crawler = None
    try:
        # Validate provider if using LLM filter
        if filter_type == FilterType.LLM:
            is_valid, error_msg = validate_llm_provider(config, provider)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_msg
                )
        decoded_url = unquote(url)
        if not decoded_url.startswith(('http://', 'https://')) and not decoded_url.startswith(("raw:", "raw://")):
            decoded_url = 'https://' + decoded_url

        if filter_type == FilterType.RAW:
            md_generator = DefaultMarkdownGenerator()
        else:
            content_filter = {
                FilterType.FIT: PruningContentFilter(),
                FilterType.BM25: BM25ContentFilter(user_query=query or ""),
                FilterType.LLM: LLMContentFilter(
                    llm_config=LLMConfig(
                        provider=provider or config["llm"]["provider"],
                        api_token=get_llm_api_key(config, provider),  # Returns None to let litellm handle it
                        temperature=temperature or get_llm_temperature(config, provider),
                        base_url=base_url or get_llm_base_url(config, provider)
                    ),
                    instruction=query or "Extract main content"
                )
            }[filter_type]
            md_generator = DefaultMarkdownGenerator(content_filter=content_filter)

        cache_mode = CacheMode.ENABLED if cache == "1" else CacheMode.WRITE_ONLY

        from crawler_pool import get_crawler, release_crawler
        from utils import load_config as _load_config
        _cfg = _load_config()
        browser_cfg = BrowserConfig(
            extra_args=_cfg["crawler"]["browser"].get("extra_args", []),
            **_cfg["crawler"]["browser"].get("kwargs", {}),
        )
        crawler = await get_crawler(browser_cfg)
        result = await crawler.arun(
            url=decoded_url,
            config=CrawlerRunConfig(
                markdown_generator=md_generator,
                scraping_strategy=LXMLWebScrapingStrategy(),
                cache_mode=cache_mode
            )
        )

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.error_message
            )

        return (result.markdown.raw_markdown
               if filter_type == FilterType.RAW
               else result.markdown.fit_markdown)

    except Exception as e:
        logger.error(f"Markdown error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    finally:
        if crawler:
            await release_crawler(crawler)