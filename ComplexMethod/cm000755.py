def from_sdk(
        cls, import_obj: Union[SdkImport, CreateImportResponse]
    ) -> "ImportModel":
        """Convert SDK Import or CreateImportResponse to our stable model."""
        # Extract entity type from union (may be None)
        entity_type = "unknown"
        if import_obj.entity:
            entity_dict = import_obj.entity.model_dump(by_alias=True, exclude_none=True)
            entity_type = entity_dict.get("type", "unknown")

        # Handle status enum
        status_str = (
            import_obj.status.value
            if hasattr(import_obj.status, "value")
            else str(import_obj.status)
        )

        # Handle format enum
        format_str = (
            import_obj.format.value
            if hasattr(import_obj.format, "value")
            else str(import_obj.format)
        )

        # Handle failed_reason enum (may be None or enum)
        failed_reason_str = ""
        if import_obj.failed_reason:
            failed_reason_str = (
                import_obj.failed_reason.value
                if hasattr(import_obj.failed_reason, "value")
                else str(import_obj.failed_reason)
            )

        return cls(
            id=import_obj.id,
            status=status_str,
            title=import_obj.title or "",
            format=format_str,
            entity_type=entity_type,
            count=int(import_obj.count or 0),
            upload_url=getattr(
                import_obj, "upload_url", None
            ),  # Only in CreateImportResponse
            upload_valid_until=getattr(
                import_obj, "upload_valid_until", None
            ),  # Only in CreateImportResponse
            failed_reason=failed_reason_str,
            failed_message=import_obj.failed_message or "",
            metadata=import_obj.metadata or {},
            created_at=(
                import_obj.created_at.isoformat() if import_obj.created_at else ""
            ),
            updated_at=(
                import_obj.updated_at.isoformat() if import_obj.updated_at else ""
            ),
        )