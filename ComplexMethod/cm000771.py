async def run(
        self, input_data: Input, *, credentials: APIKeyCredentials, **kwargs
    ) -> BlockOutput:
        aexa = AsyncExa(api_key=credentials.api_key.get_secret_value())

        webset = await aexa.websets.get(id=input_data.webset_id)

        # Extract basic info
        webset_id = webset.id
        status = (
            webset.status.value
            if hasattr(webset.status, "value")
            else str(webset.status)
        )

        # Determine entity type from searches
        entity_type = "unknown"
        searches = webset.searches or []
        if searches:
            first_search = searches[0]
            if first_search.entity:
                entity_dict = first_search.entity.model_dump(
                    by_alias=True, exclude_none=True
                )
                entity_type = entity_dict.get("type", "unknown")

        # Get sample items if requested
        sample_items_data = []
        total_items = 0

        if input_data.include_sample_items and input_data.sample_size > 0:
            items_response = await aexa.websets.items.list(
                webset_id=input_data.webset_id, limit=input_data.sample_size
            )
            sample_items_data = [
                item.model_dump(by_alias=True, exclude_none=True)
                for item in items_response.data
            ]
            total_items = len(sample_items_data)

        # Build search summary using Pydantic model
        search_summary = SearchSummaryModel(
            total_searches=0,
            completed_searches=0,
            total_items_found=0,
            queries=[],
        )
        if input_data.include_search_details and searches:
            search_summary = SearchSummaryModel(
                total_searches=len(searches),
                completed_searches=sum(
                    1
                    for s in searches
                    if (s.status.value if hasattr(s.status, "value") else str(s.status))
                    == "completed"
                ),
                total_items_found=int(
                    sum(s.progress.found if s.progress else 0 for s in searches)
                ),
                queries=[s.query for s in searches[:3]],  # First 3 queries
            )

        # Build enrichment summary using Pydantic model
        enrichment_summary = EnrichmentSummaryModel(
            total_enrichments=0,
            completed_enrichments=0,
            enrichment_types=[],
            titles=[],
        )
        enrichments = webset.enrichments or []
        if input_data.include_enrichment_details and enrichments:
            enrichment_summary = EnrichmentSummaryModel(
                total_enrichments=len(enrichments),
                completed_enrichments=sum(
                    1
                    for e in enrichments
                    if (e.status.value if hasattr(e.status, "value") else str(e.status))
                    == "completed"
                ),
                enrichment_types=list(
                    set(
                        (
                            e.format.value
                            if e.format and hasattr(e.format, "value")
                            else str(e.format) if e.format else "text"
                        )
                        for e in enrichments
                    )
                ),
                titles=[(e.title or e.description or "")[:50] for e in enrichments[:3]],
            )

        # Build monitor summary using Pydantic model
        monitors = webset.monitors or []
        next_run_dt = None
        if monitors:
            next_runs = [m.next_run_at for m in monitors if m.next_run_at]
            if next_runs:
                next_run_dt = min(next_runs)

        monitor_summary = MonitorSummaryModel(
            total_monitors=len(monitors),
            active_monitors=sum(
                1
                for m in monitors
                if (m.status.value if hasattr(m.status, "value") else str(m.status))
                == "enabled"
            ),
            next_run=next_run_dt,
        )

        # Build statistics using Pydantic model
        statistics = WebsetStatisticsModel(
            total_operations=len(searches) + len(enrichments),
            is_processing=status in ["running", "pending"],
            has_monitors=len(monitors) > 0,
            avg_items_per_search=(
                search_summary.total_items_found / len(searches) if searches else 0
            ),
        )

        yield "webset_id", webset_id
        yield "status", status
        yield "entity_type", entity_type
        yield "total_items", total_items
        yield "sample_items", sample_items_data
        yield "search_summary", search_summary
        yield "enrichment_summary", enrichment_summary
        yield "monitor_summary", monitor_summary
        yield "statistics", statistics
        yield "created_at", webset.created_at.isoformat() if webset.created_at else ""
        yield "updated_at", webset.updated_at.isoformat() if webset.updated_at else ""