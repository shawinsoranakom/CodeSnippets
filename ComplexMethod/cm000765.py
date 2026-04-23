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
                # Get current enrichment status using SDK
                enrichment = await aexa.websets.enrichments.get(
                    webset_id=input_data.webset_id, id=input_data.enrichment_id
                )

                # Extract status
                status = (
                    enrichment.status.value
                    if hasattr(enrichment.status, "value")
                    else str(enrichment.status)
                )

                # Check if enrichment is complete
                if status in ["completed", "failed", "canceled"]:
                    elapsed = time.time() - start_time

                    # Get sample enriched items if requested
                    sample_data = []
                    items_enriched = 0

                    if input_data.sample_results and status == "completed":
                        sample_data, items_enriched = (
                            await self._get_sample_enrichments(
                                input_data.webset_id, input_data.enrichment_id, aexa
                            )
                        )

                    yield "enrichment_id", input_data.enrichment_id
                    yield "final_status", status
                    yield "items_enriched", items_enriched
                    yield "enrichment_title", enrichment.title or enrichment.description or ""
                    yield "elapsed_time", elapsed
                    if input_data.sample_results:
                        yield "sample_data", sample_data
                    yield "timed_out", False

                    return

                # Wait before next check with exponential backoff
                await asyncio.sleep(interval)
                interval = min(interval * 1.5, max_interval)

            # Timeout reached
            elapsed = time.time() - start_time

            # Get last known status
            enrichment = await aexa.websets.enrichments.get(
                webset_id=input_data.webset_id, id=input_data.enrichment_id
            )
            final_status = (
                enrichment.status.value
                if hasattr(enrichment.status, "value")
                else str(enrichment.status)
            )
            title = enrichment.title or enrichment.description or ""

            yield "enrichment_id", input_data.enrichment_id
            yield "final_status", final_status
            yield "items_enriched", 0
            yield "enrichment_title", title
            yield "elapsed_time", elapsed
            yield "timed_out", True

        except asyncio.TimeoutError:
            raise ValueError(
                f"Enrichment polling timed out after {input_data.timeout} seconds"
            ) from None