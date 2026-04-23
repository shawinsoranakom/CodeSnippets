def _get_all_extensions_by_priority(self) -> list[tuple[int, str, dict | None]]:
        """Build unified list of registered and unregistered extensions sorted by priority.

        Registered extensions use their stored priority; unregistered directories
        get implicit priority=10. Results are sorted by (priority, ext_id) for
        deterministic ordering.

        Returns:
            List of (priority, ext_id, metadata_or_none) tuples sorted by priority.
        """
        if not self.extensions_dir.exists():
            return []

        registry = ExtensionRegistry(self.extensions_dir)
        # Use keys() to track ALL extensions (including corrupted entries) without deep copy
        # This prevents corrupted entries from being picked up as "unregistered" dirs
        registered_extension_ids = registry.keys()

        # Get all registered extensions including disabled; we filter disabled manually below
        all_registered = registry.list_by_priority(include_disabled=True)

        all_extensions: list[tuple[int, str, dict | None]] = []

        # Only include enabled extensions in the result
        for ext_id, metadata in all_registered:
            # Skip disabled extensions
            if not metadata.get("enabled", True):
                continue
            priority = normalize_priority(metadata.get("priority") if metadata else None)
            all_extensions.append((priority, ext_id, metadata))

        # Add unregistered directories with implicit priority=10
        for ext_dir in self.extensions_dir.iterdir():
            if not ext_dir.is_dir() or ext_dir.name.startswith("."):
                continue
            if ext_dir.name not in registered_extension_ids:
                all_extensions.append((10, ext_dir.name, None))

        # Sort by (priority, ext_id) for deterministic ordering
        all_extensions.sort(key=lambda x: (x[0], x[1]))
        return all_extensions