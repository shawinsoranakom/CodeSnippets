def resolve_with_source(
        self,
        template_name: str,
        template_type: str = "template",
    ) -> Optional[Dict[str, str]]:
        """Resolve a template name and return source attribution.

        Args:
            template_name: Template name (e.g., "spec-template")
            template_type: Template type ("template", "command", or "script")

        Returns:
            Dictionary with 'path' and 'source' keys, or None if not found
        """
        # Delegate to resolve() for the actual lookup, then determine source
        resolved = self.resolve(template_name, template_type)
        if resolved is None:
            return None

        resolved_str = str(resolved)

        # Determine source attribution
        if str(self.overrides_dir) in resolved_str:
            return {"path": resolved_str, "source": "project override"}

        if str(self.presets_dir) in resolved_str and self.presets_dir.exists():
            registry = PresetRegistry(self.presets_dir)
            for pack_id, _metadata in registry.list_by_priority():
                pack_dir = self.presets_dir / pack_id
                try:
                    resolved.relative_to(pack_dir)
                    meta = registry.get(pack_id)
                    version = meta.get("version", "?") if meta else "?"
                    return {
                        "path": resolved_str,
                        "source": f"{pack_id} v{version}",
                    }
                except ValueError:
                    continue

        for _priority, ext_id, ext_meta in self._get_all_extensions_by_priority():
            ext_dir = self.extensions_dir / ext_id
            if not ext_dir.is_dir():
                continue
            try:
                resolved.relative_to(ext_dir)
                if ext_meta:
                    version = ext_meta.get("version", "?")
                    return {
                        "path": resolved_str,
                        "source": f"extension:{ext_id} v{version}",
                    }
                else:
                    return {
                        "path": resolved_str,
                        "source": f"extension:{ext_id} (unregistered)",
                    }
            except ValueError:
                continue

        return {"path": resolved_str, "source": "core"}