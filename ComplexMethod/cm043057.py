async def process_llm_extraction(
    redis: aioredis.Redis,
    config: dict,
    task_id: str,
    url: str,
    instruction: str,
    schema: Optional[str] = None,
    cache: str = "0",
    provider: Optional[str] = None,
    webhook_config: Optional[Dict] = None,
    temperature: Optional[float] = None,
    base_url: Optional[str] = None
) -> None:
    """Process LLM extraction in background."""
    # Initialize webhook service
    webhook_service = WebhookDeliveryService(config)

    try:
        # Validate provider
        is_valid, error_msg = validate_llm_provider(config, provider)
        if not is_valid:
            await hset_with_ttl(redis, f"task:{task_id}", {
                "status": TaskStatus.FAILED,
                "error": error_msg
            }, config)

            # Send webhook notification on failure
            await webhook_service.notify_job_completion(
                task_id=task_id,
                task_type="llm_extraction",
                status="failed",
                urls=[url],
                webhook_config=webhook_config,
                error=error_msg
            )
            return
        api_key = get_llm_api_key(config, provider)  # Returns None to let litellm handle it
        llm_strategy = LLMExtractionStrategy(
            llm_config=LLMConfig(
                provider=provider or config["llm"]["provider"],
                api_token=api_key,
                temperature=temperature or get_llm_temperature(config, provider),
                base_url=base_url or get_llm_base_url(config, provider)
            ),
            instruction=instruction,
            schema=json.loads(schema) if schema else None,
        )

        cache_mode = CacheMode.ENABLED if cache == "1" else CacheMode.WRITE_ONLY

        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(
                url=url,
                config=CrawlerRunConfig(
                    extraction_strategy=llm_strategy,
                    scraping_strategy=LXMLWebScrapingStrategy(),
                    cache_mode=cache_mode
                )
            )

        if not result.success:
            await hset_with_ttl(redis, f"task:{task_id}", {
                "status": TaskStatus.FAILED,
                "error": result.error_message
            }, config)

            # Send webhook notification on failure
            await webhook_service.notify_job_completion(
                task_id=task_id,
                task_type="llm_extraction",
                status="failed",
                urls=[url],
                webhook_config=webhook_config,
                error=result.error_message
            )
            return

        try:
            content = json.loads(result.extracted_content)
        except json.JSONDecodeError:
            content = result.extracted_content

        result_data = {"extracted_content": content}

        await hset_with_ttl(redis, f"task:{task_id}", {
            "status": TaskStatus.COMPLETED,
            "result": json.dumps(content)
        }, config)

        # Send webhook notification on successful completion
        await webhook_service.notify_job_completion(
            task_id=task_id,
            task_type="llm_extraction",
            status="completed",
            urls=[url],
            webhook_config=webhook_config,
            result=result_data
        )

    except Exception as e:
        logger.error(f"LLM extraction error: {str(e)}", exc_info=True)
        await hset_with_ttl(redis, f"task:{task_id}", {
            "status": TaskStatus.FAILED,
            "error": str(e)
        }, config)

        # Send webhook notification on failure
        await webhook_service.notify_job_completion(
            task_id=task_id,
            task_type="llm_extraction",
            status="failed",
            urls=[url],
            webhook_config=webhook_config,
            error=str(e)
        )