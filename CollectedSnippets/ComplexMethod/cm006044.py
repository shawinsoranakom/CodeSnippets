def util_update_snapshot_bindings(self, *, result) -> UpdateSnapshotBindings:  # type: ignore[override]
        provider_result = result.provider_result
        if not isinstance(provider_result, dict):
            return UpdateSnapshotBindings()
        snapshot_bindings = provider_result.get("added_snapshot_bindings")
        if not isinstance(snapshot_bindings, list):
            return UpdateSnapshotBindings()
        resolved: list[UpdateSnapshotBinding] = []
        for binding in snapshot_bindings:
            if not isinstance(binding, dict):
                continue
            source_ref = str(binding.get("source_ref") or "").strip()
            snapshot_id = str(binding.get("snapshot_id") or "").strip()
            if source_ref and snapshot_id:
                resolved.append(
                    UpdateSnapshotBinding(
                        source_ref=source_ref,
                        snapshot_id=snapshot_id,
                    )
                )
        return UpdateSnapshotBindings(snapshot_bindings=resolved)