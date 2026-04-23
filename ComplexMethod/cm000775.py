async def run(
        self, input_data: Input, *, credentials: APIKeyCredentials, **kwargs
    ) -> BlockOutput:
        # Use AsyncExa SDK
        aexa = AsyncExa(api_key=credentials.api_key.get_secret_value())

        webset = await aexa.websets.get(id=input_data.webset_id)

        entity_type = "unknown"
        if webset.searches:
            first_search = webset.searches[0]
            if first_search.entity:
                # The entity is a union type, extract type field
                entity_dict = first_search.entity.model_dump(by_alias=True)
                entity_type = entity_dict.get("type", "unknown")

        # Get enrichment columns
        enrichment_columns = []
        if webset.enrichments:
            enrichment_columns = [
                e.title if e.title else e.description for e in webset.enrichments
            ]

        # Get sample items if requested
        sample_items: List[WebsetItemModel] = []
        if input_data.sample_size > 0:
            items_response = await aexa.websets.items.list(
                webset_id=input_data.webset_id, limit=input_data.sample_size
            )
            # Convert to our stable models
            sample_items = [
                WebsetItemModel.from_sdk(item) for item in items_response.data
            ]

        total_items = 0
        if webset.searches:
            for search in webset.searches:
                if search.progress:
                    total_items += search.progress.found

        yield "total_items", total_items
        yield "entity_type", entity_type
        yield "sample_items", sample_items
        yield "enrichment_columns", enrichment_columns