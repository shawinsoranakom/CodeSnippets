async def run(
        self, input_data: Input, *, credentials: APIKeyCredentials, **kwargs
    ) -> BlockOutput:
        import time

        # Build the payload
        payload = {
            "query": input_data.query,
            "count": input_data.count,
            "behavior": input_data.behavior.value,
            "recall": input_data.recall,
        }

        # Add entity configuration
        if input_data.entity_type != SearchEntityType.AUTO:
            entity = {"type": input_data.entity_type.value}
            if (
                input_data.entity_type == SearchEntityType.CUSTOM
                and input_data.entity_description
            ):
                entity["description"] = input_data.entity_description
            payload["entity"] = entity

        # Add criteria if provided
        if input_data.criteria:
            payload["criteria"] = [{"description": c} for c in input_data.criteria]

        # Add exclude sources
        if input_data.exclude_source_ids:
            exclude_list = []
            for idx, src_id in enumerate(input_data.exclude_source_ids):
                src_type = "import"
                if input_data.exclude_source_types and idx < len(
                    input_data.exclude_source_types
                ):
                    src_type = input_data.exclude_source_types[idx]
                exclude_list.append({"source": src_type, "id": src_id})
            payload["exclude"] = exclude_list

        # Add scope sources
        if input_data.scope_source_ids:
            scope_list: list[dict[str, Any]] = []
            for idx, src_id in enumerate(input_data.scope_source_ids):
                scope_item: dict[str, Any] = {"source": "import", "id": src_id}

                if input_data.scope_source_types and idx < len(
                    input_data.scope_source_types
                ):
                    scope_item["source"] = input_data.scope_source_types[idx]

                # Add relationship if provided
                if input_data.scope_relationships and idx < len(
                    input_data.scope_relationships
                ):
                    relationship: dict[str, Any] = {
                        "definition": input_data.scope_relationships[idx]
                    }
                    if input_data.scope_relationship_limits and idx < len(
                        input_data.scope_relationship_limits
                    ):
                        relationship["limit"] = input_data.scope_relationship_limits[
                            idx
                        ]
                    scope_item["relationship"] = relationship

                scope_list.append(scope_item)
            payload["scope"] = scope_list

        # Add metadata if provided
        if input_data.metadata:
            payload["metadata"] = input_data.metadata

        start_time = time.time()

        aexa = AsyncExa(api_key=credentials.api_key.get_secret_value())

        sdk_search = await aexa.websets.searches.create(
            webset_id=input_data.webset_id, params=payload
        )

        search_id = sdk_search.id
        status = (
            sdk_search.status.value
            if hasattr(sdk_search.status, "value")
            else str(sdk_search.status)
        )

        # Extract expected results from recall
        expected_results = {}
        if sdk_search.recall:
            recall_dict = sdk_search.recall.model_dump(by_alias=True)
            expected = recall_dict.get("expected", {})
            expected_results = {
                "total": expected.get("total", 0),
                "confidence": expected.get("confidence", ""),
                "min": expected.get("bounds", {}).get("min", 0),
                "max": expected.get("bounds", {}).get("max", 0),
                "reasoning": recall_dict.get("reasoning", ""),
            }

        # If wait_for_completion is True, poll for completion
        if input_data.wait_for_completion:
            import asyncio

            poll_interval = 5
            max_interval = 30
            poll_start = time.time()

            while time.time() - poll_start < input_data.polling_timeout:
                current_search = await aexa.websets.searches.get(
                    webset_id=input_data.webset_id, id=search_id
                )
                current_status = (
                    current_search.status.value
                    if hasattr(current_search.status, "value")
                    else str(current_search.status)
                )

                if current_status in ["completed", "failed", "cancelled"]:
                    items_found = 0
                    if current_search.progress:
                        items_found = current_search.progress.found
                    completion_time = time.time() - start_time

                    yield "search_id", search_id
                    yield "webset_id", input_data.webset_id
                    yield "status", current_status
                    yield "query", input_data.query
                    yield "expected_results", expected_results
                    yield "items_found", items_found
                    yield "completion_time", completion_time
                    return

                await asyncio.sleep(poll_interval)
                poll_interval = min(poll_interval * 1.5, max_interval)

            # Timeout - yield what we have
            yield "search_id", search_id
            yield "webset_id", input_data.webset_id
            yield "status", status
            yield "query", input_data.query
            yield "expected_results", expected_results
            yield "items_found", 0
            yield "completion_time", time.time() - start_time
        else:
            yield "search_id", search_id
            yield "webset_id", input_data.webset_id
            yield "status", status
            yield "query", input_data.query
            yield "expected_results", expected_results