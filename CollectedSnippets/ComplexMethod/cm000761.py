def from_sdk(cls, enrichment: SdkWebsetEnrichment) -> "WebsetEnrichmentModel":
        """Convert SDK WebsetEnrichment to our stable model."""
        # Extract options
        options_list = []
        if enrichment.options:
            for option in enrichment.options:
                option_dict = option.model_dump(by_alias=True)
                options_list.append(option_dict.get("label", ""))

        return cls(
            id=enrichment.id,
            webset_id=enrichment.webset_id,
            status=(
                enrichment.status.value
                if hasattr(enrichment.status, "value")
                else str(enrichment.status)
            ),
            title=enrichment.title,
            description=enrichment.description,
            format=(
                enrichment.format.value
                if enrichment.format and hasattr(enrichment.format, "value")
                else "text"
            ),
            options=options_list,
            instructions=enrichment.instructions,
            metadata=enrichment.metadata if enrichment.metadata else {},
            created_at=(
                enrichment.created_at.isoformat() if enrichment.created_at else ""
            ),
            updated_at=(
                enrichment.updated_at.isoformat() if enrichment.updated_at else ""
            ),
        )