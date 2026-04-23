async def run(
        self, input_data: Input, *, credentials: APIKeyCredentials, **kwargs
    ) -> BlockOutput:
        aexa = AsyncExa(api_key=credentials.api_key.get_secret_value())

        webset = await aexa.websets.get(id=input_data.webset_id)

        status = (
            webset.status.value
            if hasattr(webset.status, "value")
            else str(webset.status)
        )
        is_processing = status in ["running", "pending"]

        # Estimate item count from search progress
        item_count = 0
        if webset.searches:
            for search in webset.searches:
                if search.progress:
                    item_count += search.progress.found

        # Count searches, enrichments, monitors
        search_count = len(webset.searches or [])
        enrichment_count = len(webset.enrichments or [])
        monitor_count = len(webset.monitors or [])

        yield "webset_id", webset.id
        yield "status", status
        yield "item_count", item_count
        yield "search_count", search_count
        yield "enrichment_count", enrichment_count
        yield "monitor_count", monitor_count
        yield "last_updated", webset.updated_at.isoformat() if webset.updated_at else ""
        yield "is_processing", is_processing