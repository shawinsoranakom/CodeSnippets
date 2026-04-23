async def stream_results(crawler: AsyncWebCrawler, results_gen: AsyncGenerator) -> AsyncGenerator[bytes, None]:
    """Stream results with heartbeats and completion markers."""
    import json
    from utils import datetime_handler
    from crawler_pool import release_crawler

    try:
        async for result in results_gen:
            try:
                server_memory_mb = _get_memory_mb()
                result_dict = result.model_dump()
                result_dict['server_memory_mb'] = server_memory_mb
                # Ensure fit_html is JSON-serializable
                if "fit_html" in result_dict and not (result_dict["fit_html"] is None or isinstance(result_dict["fit_html"], str)):
                    result_dict["fit_html"] = None
                # If PDF exists, encode it to base64
                if result_dict.get('pdf') is not None:
                    result_dict['pdf'] = b64encode(result_dict['pdf']).decode('utf-8')
                logger.info(f"Streaming result for {result_dict.get('url', 'unknown')}")
                data = json.dumps(result_dict, default=datetime_handler) + "\n"
                yield data.encode('utf-8')
            except Exception as e:
                logger.error(f"Serialization error: {e}")
                error_response = {"error": str(e), "url": getattr(result, 'url', 'unknown')}
                yield (json.dumps(error_response) + "\n").encode('utf-8')

        yield json.dumps({"status": "completed"}).encode('utf-8')

    except asyncio.CancelledError:
        logger.warning("Client disconnected during streaming")
    finally:
        if crawler:
            await release_crawler(crawler)