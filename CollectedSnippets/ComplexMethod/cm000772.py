async def run(
        self, input_data: Input, *, credentials: APIKeyCredentials, **kwargs
    ) -> BlockOutput:
        aexa = AsyncExa(api_key=credentials.api_key.get_secret_value())

        # Get webset details
        webset = await aexa.websets.get(id=input_data.webset_id)

        status = (
            webset.status.value
            if hasattr(webset.status, "value")
            else str(webset.status)
        )

        # Estimate item count from search progress
        item_count = 0
        if webset.searches:
            for search in webset.searches:
                if search.progress:
                    item_count += search.progress.found

        # Determine readiness
        is_idle = status == "idle"
        has_min_items = item_count >= input_data.min_items
        is_ready = is_idle and has_min_items

        # Check resources
        has_searches = len(webset.searches or []) > 0
        has_enrichments = len(webset.enrichments or []) > 0

        # Generate recommendation
        recommendation = ""
        if not has_searches:
            recommendation = "needs_search"
        elif status in ["running", "pending"]:
            recommendation = "waiting_for_results"
        elif not has_min_items:
            recommendation = "insufficient_items"
        elif not has_enrichments:
            recommendation = "ready_to_enrich"
        else:
            recommendation = "ready_to_process"

        yield "is_ready", is_ready
        yield "status", status
        yield "item_count", item_count
        yield "has_searches", has_searches
        yield "has_enrichments", has_enrichments
        yield "recommendation", recommendation