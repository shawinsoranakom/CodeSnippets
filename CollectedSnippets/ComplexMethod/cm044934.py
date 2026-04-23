def resolve_extension_command_via_manifest(self, cmd_name: str) -> Optional[Path]:
        """Resolve an extension command by consulting installed extension manifests.

        Walks installed extension directories in priority order, loads each
        extension.yml via ExtensionManifest, and looks up the command by its
        declared name to find the actual file path.  This is necessary because
        the manifest's ``provides.commands[].file`` field is authoritative and
        may differ from the command name
        (e.g. ``speckit.selftest.extension`` → ``commands/selftest.md``).

        Returns None if no manifest maps the given command name, so the caller
        can fall back to the name-based lookup.
        """
        if not self.extensions_dir.exists():
            return None

        from .extensions import ExtensionManifest, ValidationError

        for _priority, ext_id, _metadata in self._get_all_extensions_by_priority():
            ext_dir = self.extensions_dir / ext_id
            manifest_path = ext_dir / "extension.yml"
            if not manifest_path.is_file():
                continue
            try:
                manifest = ExtensionManifest(manifest_path)
            except (ValidationError, OSError, TypeError, AttributeError):
                continue
            for cmd_info in manifest.commands:
                if cmd_info.get("name") != cmd_name:
                    continue
                file_rel = cmd_info.get("file")
                if not file_rel:
                    continue
                # Mirror the containment check in ExtensionManager to guard against
                # path traversal via a malformed manifest (e.g. file: ../../AGENTS.md).
                cmd_path = Path(file_rel)
                if cmd_path.is_absolute():
                    continue
                try:
                    ext_root = ext_dir.resolve()
                    candidate = (ext_root / cmd_path).resolve()
                    candidate.relative_to(ext_root)  # raises ValueError if outside
                except (OSError, ValueError):
                    continue
                if candidate.is_file():
                    return candidate
        return None