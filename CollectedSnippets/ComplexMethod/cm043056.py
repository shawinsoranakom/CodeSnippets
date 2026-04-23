async def handle_llm_qa(
    url: str,
    query: str,
    config: dict,
    provider: Optional[str] = None,
    temperature: Optional[float] = None,
    base_url: Optional[str] = None,
) -> str:
    """Process QA using LLM with crawled content as context."""
    from crawler_pool import get_crawler, release_crawler
    crawler = None
    try:
        if not url.startswith(('http://', 'https://')) and not url.startswith(("raw:", "raw://")):
            url = 'https://' + url
        # Extract base URL by finding last '?q=' occurrence
        last_q_index = url.rfind('?q=')
        if last_q_index != -1:
            url = url[:last_q_index]

        # Get markdown content (use default config)
        from utils import load_config
        cfg = load_config()
        browser_cfg = BrowserConfig(
            extra_args=cfg["crawler"]["browser"].get("extra_args", []),
            **cfg["crawler"]["browser"].get("kwargs", {}),
        )
        crawler = await get_crawler(browser_cfg)
        result = await crawler.arun(url)
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.error_message
            )
        content = result.markdown.fit_markdown or result.markdown.raw_markdown

        # Create prompt and get LLM response
        prompt = f"""Use the following content as context to answer the question.
    Content:
    {content}

    Question: {query}

    Answer:"""

        resolved_provider = provider or config["llm"]["provider"]
        response = perform_completion_with_backoff(
            provider=resolved_provider,
            prompt_with_variables=prompt,
            api_token=get_llm_api_key(config, resolved_provider),
            temperature=temperature or get_llm_temperature(config, resolved_provider),
            base_url=base_url or get_llm_base_url(config, resolved_provider),
            base_delay=config["llm"].get("backoff_base_delay", 2),
            max_attempts=config["llm"].get("backoff_max_attempts", 3),
            exponential_factor=config["llm"].get("backoff_exponential_factor", 2)
        )

        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"QA processing error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    finally:
        if crawler:
            await release_crawler(crawler)