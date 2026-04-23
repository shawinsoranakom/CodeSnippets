def from_sdk(cls, search: SdkWebsetSearch) -> "WebsetSearchModel":
        """Convert SDK WebsetSearch to our stable model."""
        # Extract entity type
        entity_type = "auto"
        if search.entity:
            entity_dict = search.entity.model_dump(by_alias=True)
            entity_type = entity_dict.get("type", "auto")

        # Convert criteria
        criteria = [c.model_dump(by_alias=True) for c in search.criteria]

        # Convert progress
        progress_dict = {}
        if search.progress:
            progress_dict = search.progress.model_dump(by_alias=True)

        # Convert recall
        recall_dict = None
        if search.recall:
            recall_dict = search.recall.model_dump(by_alias=True)

        return cls(
            id=search.id,
            webset_id=search.webset_id,
            status=(
                search.status.value
                if hasattr(search.status, "value")
                else str(search.status)
            ),
            query=search.query,
            entity_type=entity_type,
            criteria=criteria,
            count=search.count,
            behavior=search.behavior.value if search.behavior else "override",
            progress=progress_dict,
            recall=recall_dict,
            created_at=search.created_at.isoformat() if search.created_at else "",
            updated_at=search.updated_at.isoformat() if search.updated_at else "",
            canceled_at=search.canceled_at.isoformat() if search.canceled_at else None,
            canceled_reason=(
                search.canceled_reason.value if search.canceled_reason else None
            ),
            metadata=search.metadata if search.metadata else {},
        )