async def run(
        self, input_data: Input, *, credentials: APIKeyCredentials, **kwargs
    ) -> BlockOutput:
        start_time = time.time()
        interval = input_data.check_interval
        max_interval = 30
        # Use AsyncExa SDK
        aexa = AsyncExa(api_key=credentials.api_key.get_secret_value())

        try:
            while time.time() - start_time < input_data.timeout:
                # Get current search status using SDK
                search = await aexa.websets.searches.get(
                    webset_id=input_data.webset_id, id=input_data.search_id
                )

                # Extract status
                status = (
                    search.status.value
                    if hasattr(search.status, "value")
                    else str(search.status)
                )

                # Check if search is complete
                if status in ["completed", "failed", "canceled"]:
                    elapsed = time.time() - start_time

                    # Extract progress information
                    progress_dict = {}
                    if search.progress:
                        progress_dict = search.progress.model_dump(
                            by_alias=True, exclude_none=True
                        )

                    # Extract recall information
                    recall_info = {}
                    if search.recall:
                        recall_dict = search.recall.model_dump(
                            by_alias=True, exclude_none=True
                        )
                        expected = recall_dict.get("expected", {})
                        recall_info = {
                            "expected_total": expected.get("total", 0),
                            "confidence": expected.get("confidence", ""),
                            "min_expected": expected.get("bounds", {}).get("min", 0),
                            "max_expected": expected.get("bounds", {}).get("max", 0),
                            "reasoning": recall_dict.get("reasoning", ""),
                        }

                    yield "search_id", input_data.search_id
                    yield "final_status", status
                    yield "items_found", progress_dict.get("found", 0)
                    yield "items_analyzed", progress_dict.get("analyzed", 0)
                    yield "completion_percentage", progress_dict.get("completion", 0)
                    yield "elapsed_time", elapsed
                    yield "recall_info", recall_info
                    yield "timed_out", False

                    return

                # Wait before next check with exponential backoff
                await asyncio.sleep(interval)
                interval = min(interval * 1.5, max_interval)

            # Timeout reached
            elapsed = time.time() - start_time

            # Get last known status
            search = await aexa.websets.searches.get(
                webset_id=input_data.webset_id, id=input_data.search_id
            )
            final_status = (
                search.status.value
                if hasattr(search.status, "value")
                else str(search.status)
            )

            progress_dict = {}
            if search.progress:
                progress_dict = search.progress.model_dump(
                    by_alias=True, exclude_none=True
                )

            yield "search_id", input_data.search_id
            yield "final_status", final_status
            yield "items_found", progress_dict.get("found", 0)
            yield "items_analyzed", progress_dict.get("analyzed", 0)
            yield "completion_percentage", progress_dict.get("completion", 0)
            yield "elapsed_time", elapsed
            yield "timed_out", True

        except asyncio.TimeoutError:
            raise ValueError(
                f"Search polling timed out after {input_data.timeout} seconds"
            ) from None