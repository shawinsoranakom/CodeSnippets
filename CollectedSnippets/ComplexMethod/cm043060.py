async def handle_crawl_request(
    urls: List[str],
    browser_config: dict,
    crawler_config: dict,
    config: dict,
    hooks_config: Optional[dict] = None
) -> dict:
    """Handle non-streaming crawl requests with optional hooks."""
    # Track request start
    request_id = f"req_{uuid4().hex[:8]}"
    crawler = None
    try:
        from monitor import get_monitor
        await get_monitor().track_request_start(
            request_id, "/crawl", urls[0] if urls else "batch", browser_config
        )
    except:
        pass  # Monitor not critical

    start_mem_mb = _get_memory_mb() # <--- Get memory before
    start_time = time.time()
    mem_delta_mb = None
    peak_mem_mb = start_mem_mb
    hook_manager = None

    try:
        urls = [('https://' + url) if not url.startswith(('http://', 'https://')) and not url.startswith(("raw:", "raw://")) else url for url in urls]
        browser_config = BrowserConfig.load(browser_config)
        crawler_config = CrawlerRunConfig.load(crawler_config)

        dispatcher = MemoryAdaptiveDispatcher(
            memory_threshold_percent=config["crawler"]["memory_threshold_percent"],
            rate_limiter=RateLimiter(
                base_delay=tuple(config["crawler"]["rate_limiter"]["base_delay"])
            ) if config["crawler"]["rate_limiter"]["enabled"] else None
        )

        from crawler_pool import get_crawler, release_crawler
        crawler = await get_crawler(browser_config)

        # Attach hooks if provided
        hooks_status = {}
        if hooks_config:
            from hook_manager import attach_user_hooks_to_crawler, UserHookManager
            hook_manager = UserHookManager(timeout=hooks_config.get('timeout', 30))
            hooks_status, hook_manager = await attach_user_hooks_to_crawler(
                crawler,
                hooks_config.get('code', {}),
                timeout=hooks_config.get('timeout', 30),
                hook_manager=hook_manager
            )
            logger.info(f"Hooks attachment status: {hooks_status['status']}")

        base_config = config["crawler"]["base_config"]
        # Iterate on key-value pairs in global_config then use hasattr to set them
        for key, value in base_config.items():
            if hasattr(crawler_config, key):
                current_value = getattr(crawler_config, key)
                # Only set base config if user didn't provide a value
                if current_value is None or current_value == "":
                    setattr(crawler_config, key, value)

        results = []
        func = getattr(crawler, "arun" if len(urls) == 1 else "arun_many")
        partial_func = partial(func, 
                                urls[0] if len(urls) == 1 else urls, 
                                config=crawler_config, 
                                dispatcher=dispatcher)
        results = await partial_func()

        # Ensure results is always a list
        if not isinstance(results, list):
            results = [results]

        end_mem_mb = _get_memory_mb() # <--- Get memory after
        end_time = time.time()

        if start_mem_mb is not None and end_mem_mb is not None:
            mem_delta_mb = end_mem_mb - start_mem_mb # <--- Calculate delta
            peak_mem_mb = max(peak_mem_mb if peak_mem_mb else 0, end_mem_mb) # <--- Get peak memory
        logger.info(f"Memory usage: Start: {start_mem_mb} MB, End: {end_mem_mb} MB, Delta: {mem_delta_mb} MB, Peak: {peak_mem_mb} MB")

        # Process results to handle PDF bytes
        processed_results = []
        for result in results:
            try:
                # Check if result has model_dump method (is a proper CrawlResult)
                if hasattr(result, 'model_dump'):
                    result_dict = result.model_dump()
                elif isinstance(result, dict):
                    result_dict = result
                else:
                    # Handle unexpected result type
                    logger.warning(f"Unexpected result type: {type(result)}")
                    result_dict = {
                        "url": str(result) if hasattr(result, '__str__') else "unknown",
                        "success": False,
                        "error_message": f"Unexpected result type: {type(result).__name__}"
                    }

                # if fit_html is not a string, set it to None to avoid serialization errors
                if "fit_html" in result_dict and not (result_dict["fit_html"] is None or isinstance(result_dict["fit_html"], str)):
                    result_dict["fit_html"] = None

                # If PDF exists, encode it to base64
                if result_dict.get('pdf') is not None and isinstance(result_dict.get('pdf'), bytes):
                    result_dict['pdf'] = b64encode(result_dict['pdf']).decode('utf-8')

                processed_results.append(result_dict)
            except Exception as e:
                logger.error(f"Error processing result: {e}")
                processed_results.append({
                    "url": "unknown",
                    "success": False,
                    "error_message": str(e)
                })

        response = {
            "success": True,
            "results": processed_results,
            "server_processing_time_s": end_time - start_time,
            "server_memory_delta_mb": mem_delta_mb,
            "server_peak_memory_mb": peak_mem_mb
        }

        # Track request completion
        try:
            from monitor import get_monitor
            await get_monitor().track_request_end(
                request_id, success=True, pool_hit=True, status_code=200
            )
        except:
            pass

        # Add hooks information if hooks were used
        if hooks_config and hook_manager:
            from hook_manager import UserHookManager
            if isinstance(hook_manager, UserHookManager):
                try:
                    # Ensure all hook data is JSON serializable
                    hook_data = {
                        "status": hooks_status,
                        "execution_log": hook_manager.execution_log,
                        "errors": hook_manager.errors,
                        "summary": hook_manager.get_summary()
                    }
                    # Test that it's serializable
                    json.dumps(hook_data)
                    response["hooks"] = hook_data
                except (TypeError, ValueError) as e:
                    logger.error(f"Hook data not JSON serializable: {e}")
                    response["hooks"] = {
                        "status": {"status": "error", "message": "Hook data serialization failed"},
                        "execution_log": [],
                        "errors": [{"error": str(e)}],
                        "summary": {}
                    }

        return response

    except Exception as e:
        logger.error(f"Crawl error: {str(e)}", exc_info=True)

        # Track request error
        try:
            from monitor import get_monitor
            await get_monitor().track_request_end(
                request_id, success=False, error=str(e), status_code=500
            )
        except:
            pass

        # Measure memory even on error if possible
        end_mem_mb_error = _get_memory_mb()
        if start_mem_mb is not None and end_mem_mb_error is not None:
            mem_delta_mb = end_mem_mb_error - start_mem_mb

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=json.dumps({ # Send structured error
                "error": str(e),
                "server_memory_delta_mb": mem_delta_mb,
                "server_peak_memory_mb": max(peak_mem_mb if peak_mem_mb else 0, end_mem_mb_error or 0)
            })
        )
    finally:
        if crawler:
            await release_crawler(crawler)