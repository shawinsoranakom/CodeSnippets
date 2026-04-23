def shape_snapshot_list_result(
        self,
        result: SnapshotListResult,
        *,
        page: int,
        size: int,
    ) -> DeploymentSnapshotListResponse:
        slot = self.api_payloads.snapshot_list_result
        if slot is None:
            msg = "Watsonx snapshot_list_result payload slot is not configured."
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=msg)

        items_all: list[dict[str, Any]] = []
        for item in result.snapshots:
            item_provider_data = item.provider_data if isinstance(item.provider_data, dict) else {}
            connections = item_provider_data.get("connections")
            items_all.append(
                {
                    "id": str(item.id).strip(),
                    "name": str(item.name or "").strip(),
                    "connections": connections if isinstance(connections, dict) else {},
                }
            )

        total = len(items_all)
        offset = page_offset(page, size)
        provider_payload = {
            "tools": items_all[offset : offset + size],
            "page": page,
            "size": size,
            "total": total,
        }
        try:
            validated_payload = slot.parse(provider_payload).model_dump(mode="json", exclude_none=True)
        except AdapterPayloadValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Invalid snapshot list provider_data payload: {exc.format_first_error()}",
            ) from exc

        return DeploymentSnapshotListResponse(provider_data=validated_payload or None)