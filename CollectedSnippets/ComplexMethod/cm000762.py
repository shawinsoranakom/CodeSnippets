async def run(
        self, input_data: Input, *, credentials: APIKeyCredentials, **kwargs
    ) -> BlockOutput:
        import time

        # Build the payload
        payload: dict[str, Any] = {
            "description": input_data.description,
            "format": input_data.format.value,
        }

        # Add title if provided
        if input_data.title:
            payload["title"] = input_data.title

        # Add options for 'options' format
        if input_data.format == EnrichmentFormat.OPTIONS and input_data.options:
            payload["options"] = [{"label": opt} for opt in input_data.options]

        # Add metadata if provided
        if input_data.metadata:
            payload["metadata"] = input_data.metadata

        start_time = time.time()

        # Use AsyncExa SDK
        aexa = AsyncExa(api_key=credentials.api_key.get_secret_value())

        sdk_enrichment = await aexa.websets.enrichments.create(
            webset_id=input_data.webset_id, params=payload
        )

        enrichment_id = sdk_enrichment.id
        status = (
            sdk_enrichment.status.value
            if hasattr(sdk_enrichment.status, "value")
            else str(sdk_enrichment.status)
        )

        # If wait_for_completion is True and apply_to_existing is True, poll for completion
        if input_data.wait_for_completion and input_data.apply_to_existing:
            import asyncio

            poll_interval = 5
            max_interval = 30
            poll_start = time.time()
            items_enriched = 0

            while time.time() - poll_start < input_data.polling_timeout:
                current_enrich = await aexa.websets.enrichments.get(
                    webset_id=input_data.webset_id, id=enrichment_id
                )
                current_status = (
                    current_enrich.status.value
                    if hasattr(current_enrich.status, "value")
                    else str(current_enrich.status)
                )

                if current_status in ["completed", "failed", "cancelled"]:
                    # Estimate items from webset searches
                    webset = await aexa.websets.get(id=input_data.webset_id)
                    if webset.searches:
                        for search in webset.searches:
                            if search.progress:
                                items_enriched += search.progress.found
                    completion_time = time.time() - start_time

                    yield "enrichment_id", enrichment_id
                    yield "webset_id", input_data.webset_id
                    yield "status", current_status
                    yield "title", sdk_enrichment.title
                    yield "description", input_data.description
                    yield "format", input_data.format.value
                    yield "instructions", sdk_enrichment.instructions
                    yield "items_enriched", items_enriched
                    yield "completion_time", completion_time
                    return

                await asyncio.sleep(poll_interval)
                poll_interval = min(poll_interval * 1.5, max_interval)

            # Timeout
            completion_time = time.time() - start_time
            yield "enrichment_id", enrichment_id
            yield "webset_id", input_data.webset_id
            yield "status", status
            yield "title", sdk_enrichment.title
            yield "description", input_data.description
            yield "format", input_data.format.value
            yield "instructions", sdk_enrichment.instructions
            yield "items_enriched", 0
            yield "completion_time", completion_time
        else:
            yield "enrichment_id", enrichment_id
            yield "webset_id", input_data.webset_id
            yield "status", status
            yield "title", sdk_enrichment.title
            yield "description", input_data.description
            yield "format", input_data.format.value
            yield "instructions", sdk_enrichment.instructions