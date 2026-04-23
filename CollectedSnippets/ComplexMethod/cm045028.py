def _get_merged_workflows(
        self, force_refresh: bool = False
    ) -> dict[str, dict[str, Any]]:
        """Merge workflows from all active catalogs (lower priority number wins)."""
        catalogs = self.get_active_catalogs()
        merged: dict[str, dict[str, Any]] = {}
        fetch_errors = 0

        # Process later/higher-numbered entries first so earlier/lower-numbered
        # entries overwrite them on workflow ID conflicts.
        for entry in reversed(catalogs):
            try:
                data = self._fetch_single_catalog(entry, force_refresh)
            except WorkflowCatalogError:
                fetch_errors += 1
                continue
            workflows = data.get("workflows", {})
            # Handle both dict and list formats
            if isinstance(workflows, dict):
                for wf_id, wf_data in workflows.items():
                    if not isinstance(wf_data, dict):
                        continue
                    wf_data["_catalog_name"] = entry.name
                    wf_data["_install_allowed"] = entry.install_allowed
                    merged[wf_id] = wf_data
            elif isinstance(workflows, list):
                for wf_data in workflows:
                    if not isinstance(wf_data, dict):
                        continue
                    wf_id = wf_data.get("id", "")
                    if wf_id:
                        wf_data["_catalog_name"] = entry.name
                        wf_data["_install_allowed"] = entry.install_allowed
                        merged[wf_id] = wf_data
        if fetch_errors == len(catalogs) and catalogs:
            raise WorkflowCatalogError(
                "All configured catalogs failed to fetch."
            )
        return merged