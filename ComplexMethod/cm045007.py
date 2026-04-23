def _get_merged_integrations(
        self, force_refresh: bool = False
    ) -> List[Dict[str, Any]]:
        """Fetch and merge integrations from all active catalogs.

        Catalogs are processed in the order returned by
        :meth:`get_active_catalogs`.  On conflicts, the first catalog in that
        order wins (lower numeric priority = higher precedence).  Each dict is
        annotated with ``_catalog_name`` and ``_install_allowed``.
        """
        import sys

        active = self.get_active_catalogs()
        merged: Dict[str, Dict[str, Any]] = {}
        any_success = False

        for entry in active:
            try:
                data = self._fetch_single_catalog(entry, force_refresh)
                any_success = True
            except IntegrationCatalogError as exc:
                print(
                    f"Warning: Could not fetch catalog '{entry.name}': {exc}",
                    file=sys.stderr,
                )
                continue

            for integ_id, integ_data in data.get("integrations", {}).items():
                if not isinstance(integ_data, dict):
                    continue
                if integ_id not in merged:
                    merged[integ_id] = {
                        **integ_data,
                        "id": integ_id,
                        "_catalog_name": entry.name,
                        "_install_allowed": entry.install_allowed,
                    }

        if not any_success and active:
            raise IntegrationCatalogError(
                "Failed to fetch any integration catalog"
            )

        return list(merged.values())