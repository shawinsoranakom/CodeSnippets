def _resolve_flow_version_item_data_by_snapshot_id(
        self,
        *,
        snapshot_result: SnapshotListResult | None,
    ) -> dict[str, dict[str, Any]]:
        """Build API flow-version item provider_data keyed by snapshot id."""
        if snapshot_result is None:
            return {}
        if not snapshot_result.snapshots:
            return {}

        item_data_by_snapshot_id: dict[str, dict[str, Any]] = {}
        for snapshot in snapshot_result.snapshots:
            snapshot_id = str(snapshot.id).strip()
            if not snapshot_id:
                msg = "Invalid flow-version provider_data payload: snapshot id must be a non-empty string."
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=msg)

            provider_data = snapshot.provider_data

            if not isinstance(provider_data, dict) or not provider_data:
                msg = "Invalid flow-version provider_data payload: snapshot provider_data must be a non-empty object."
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=msg)

            raw_connections = provider_data.get("connections")
            if not isinstance(raw_connections, dict):
                msg = "Invalid flow-version provider_data payload: connections must be a dict."
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=msg)

            try:
                item_data_by_snapshot_id[snapshot_id] = self._validate_slot(
                    self.api_payloads.deployment_item_data,
                    {
                        "app_ids": list(raw_connections.keys()),
                        "tool_name": snapshot.name,
                    },
                )
            except AdapterPayloadValidationError as exc:
                detail = exc.format_first_error()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Invalid flow-version provider_data payload: {detail}",
                ) from exc

        return item_data_by_snapshot_id