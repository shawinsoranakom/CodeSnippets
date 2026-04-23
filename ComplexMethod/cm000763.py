async def run(
        self, input_data: Input, *, credentials: APIKeyCredentials, **kwargs
    ) -> BlockOutput:
        start_time = time.time()
        aexa = AsyncExa(api_key=credentials.api_key.get_secret_value())

        try:
            if input_data.target_status in [
                WebsetTargetStatus.IDLE,
                WebsetTargetStatus.ANY_COMPLETE,
            ]:
                final_webset = await aexa.websets.wait_until_idle(
                    id=input_data.webset_id,
                    timeout=input_data.timeout,
                    poll_interval=input_data.check_interval,
                )

                elapsed = time.time() - start_time

                status_str = (
                    final_webset.status.value
                    if hasattr(final_webset.status, "value")
                    else str(final_webset.status)
                )

                item_count = 0
                if final_webset.searches:
                    for search in final_webset.searches:
                        if search.progress:
                            item_count += search.progress.found

                # Extract progress if requested
                search_progress = {}
                enrichment_progress = {}
                if input_data.include_progress:
                    webset_dict = final_webset.model_dump(
                        by_alias=True, exclude_none=True
                    )
                    search_progress = self._extract_search_progress(webset_dict)
                    enrichment_progress = self._extract_enrichment_progress(webset_dict)

                yield "webset_id", input_data.webset_id
                yield "final_status", status_str
                yield "elapsed_time", elapsed
                yield "item_count", item_count
                if input_data.include_progress:
                    yield "search_progress", search_progress
                    yield "enrichment_progress", enrichment_progress
                yield "timed_out", False
            else:
                # For other status targets, manually poll
                interval = input_data.check_interval
                while time.time() - start_time < input_data.timeout:
                    # Get current webset status
                    webset = await aexa.websets.get(id=input_data.webset_id)
                    current_status = (
                        webset.status.value
                        if hasattr(webset.status, "value")
                        else str(webset.status)
                    )

                    # Check if target status reached
                    if current_status == input_data.target_status.value:
                        elapsed = time.time() - start_time

                        # Estimate item count from search progress
                        item_count = 0
                        if webset.searches:
                            for search in webset.searches:
                                if search.progress:
                                    item_count += search.progress.found

                        search_progress = {}
                        enrichment_progress = {}
                        if input_data.include_progress:
                            webset_dict = webset.model_dump(
                                by_alias=True, exclude_none=True
                            )
                            search_progress = self._extract_search_progress(webset_dict)
                            enrichment_progress = self._extract_enrichment_progress(
                                webset_dict
                            )

                        yield "webset_id", input_data.webset_id
                        yield "final_status", current_status
                        yield "elapsed_time", elapsed
                        yield "item_count", item_count
                        if input_data.include_progress:
                            yield "search_progress", search_progress
                            yield "enrichment_progress", enrichment_progress
                        yield "timed_out", False
                        return

                    # Wait before next check with exponential backoff
                    await asyncio.sleep(interval)
                    interval = min(interval * 1.5, input_data.max_interval)

                # Timeout reached
                elapsed = time.time() - start_time
                webset = await aexa.websets.get(id=input_data.webset_id)
                final_status = (
                    webset.status.value
                    if hasattr(webset.status, "value")
                    else str(webset.status)
                )

                item_count = 0
                if webset.searches:
                    for search in webset.searches:
                        if search.progress:
                            item_count += search.progress.found

                search_progress = {}
                enrichment_progress = {}
                if input_data.include_progress:
                    webset_dict = webset.model_dump(by_alias=True, exclude_none=True)
                    search_progress = self._extract_search_progress(webset_dict)
                    enrichment_progress = self._extract_enrichment_progress(webset_dict)

                yield "webset_id", input_data.webset_id
                yield "final_status", final_status
                yield "elapsed_time", elapsed
                yield "item_count", item_count
                if input_data.include_progress:
                    yield "search_progress", search_progress
                    yield "enrichment_progress", enrichment_progress
                yield "timed_out", True

        except asyncio.TimeoutError:
            raise ValueError(
                f"Polling timed out after {input_data.timeout} seconds"
            ) from None