def from_sdk(cls, item: SdkWebsetItem) -> "WebsetItemModel":
        """Convert SDK WebsetItem to our stable model."""
        # Extract properties from the union type
        properties_dict = {}
        url_value = None
        title = ""
        content = ""

        if hasattr(item, "properties") and item.properties:
            properties_dict = item.properties.model_dump(
                by_alias=True, exclude_none=True
            )

            # URL is always available on all property types
            url_value = item.properties.url

            # Extract title using isinstance checks on the union type
            if isinstance(item.properties, WebsetItemPersonProperties):
                title = item.properties.person.name
                content = ""  # Person type has no content
            elif isinstance(item.properties, WebsetItemCompanyProperties):
                title = item.properties.company.name
                content = item.properties.content or ""
            elif isinstance(item.properties, WebsetItemArticleProperties):
                title = item.properties.description
                content = item.properties.content or ""
            elif isinstance(item.properties, WebsetItemResearchPaperProperties):
                title = item.properties.description
                content = item.properties.content or ""
            elif isinstance(item.properties, WebsetItemCustomProperties):
                title = item.properties.description
                content = item.properties.content or ""
            else:
                # Fallback
                title = item.properties.description
                content = getattr(item.properties, "content", "")

        # Convert enrichments from list to dict keyed by enrichment_id using Pydantic models
        enrichments_dict: Dict[str, EnrichmentResultModel] = {}
        if hasattr(item, "enrichments") and item.enrichments:
            for sdk_enrich in item.enrichments:
                enrich_model = EnrichmentResultModel.from_sdk(sdk_enrich)
                enrichments_dict[enrich_model.enrichment_id] = enrich_model

        return cls(
            id=item.id,
            url=url_value,
            title=title,
            content=content or "",
            entity_data=properties_dict,
            enrichments=enrichments_dict,
            created_at=item.created_at.isoformat() if item.created_at else "",
            updated_at=item.updated_at.isoformat() if item.updated_at else "",
        )