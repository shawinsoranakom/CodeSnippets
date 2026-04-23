async def run(
        self, input_data: Input, *, credentials: APIKeyCredentials, **kwargs
    ) -> BlockOutput:
        aexa = AsyncExa(api_key=credentials.api_key.get_secret_value())

        payload: dict[str, Any] = {
            "query": input_data.query,
        }

        if input_data.entity_type:
            entity: dict[str, Any] = {"type": input_data.entity_type.value}
            if (
                input_data.entity_type == SearchEntityType.CUSTOM
                and input_data.entity_description
            ):
                entity["description"] = input_data.entity_description
            payload["entity"] = entity

        sdk_preview = await aexa.websets.preview(params=payload)

        preview = PreviewWebsetModel.from_sdk(sdk_preview)

        entity_type = preview.search.entity_type
        entity_description = preview.search.entity_description
        criteria = preview.search.criteria
        enrichments = preview.enrichments

        # Generate interpretation
        interpretation = f"Query will search for {entity_type}"
        if entity_description:
            interpretation += f" ({entity_description})"
        if criteria:
            interpretation += f" with {len(criteria)} criteria"
        if enrichments:
            interpretation += f" and {len(enrichments)} available enrichment columns"

        # Generate suggestions
        suggestions = []
        if not criteria:
            suggestions.append(
                "Consider adding specific criteria to narrow your search"
            )
        if not enrichments:
            suggestions.append(
                "Consider specifying what data points you want to extract"
            )

        # Yield full model first
        yield "preview", preview

        # Then yield individual fields for graph flexibility
        yield "entity_type", entity_type
        yield "entity_description", entity_description
        yield "criteria", criteria
        yield "enrichment_columns", enrichments
        yield "interpretation", interpretation
        yield "suggestions", suggestions