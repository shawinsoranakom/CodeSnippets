def remove_catalog(self, index: int) -> str:
        """Remove a catalog source by index (0-based). Returns the removed name."""
        config_path = self.project_root / ".specify" / "workflow-catalogs.yml"
        if not config_path.exists():
            raise WorkflowValidationError("No catalog config file found.")

        data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        if not isinstance(data, dict):
            raise WorkflowValidationError(
                "Catalog config file is corrupted (expected a mapping)."
            )
        catalogs = data.get("catalogs", [])
        if not isinstance(catalogs, list):
            raise WorkflowValidationError(
                "Catalog config 'catalogs' must be a list."
            )

        if index < 0 or index >= len(catalogs):
            raise WorkflowValidationError(
                f"Catalog index {index} out of range (0-{len(catalogs) - 1})."
            )

        removed = catalogs.pop(index)
        data["catalogs"] = catalogs

        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

        if isinstance(removed, dict):
            return removed.get("name", f"catalog-{index + 1}")
        return f"catalog-{index + 1}"