def install_from_directory(
        self,
        source_dir: Path,
        speckit_version: str,
        priority: int = 10,
    ) -> PresetManifest:
        """Install preset from a local directory.

        Args:
            source_dir: Path to preset directory
            speckit_version: Current spec-kit version
            priority: Resolution priority (lower = higher precedence, default 10)

        Returns:
            Installed preset manifest

        Raises:
            PresetValidationError: If manifest is invalid or priority is invalid
            PresetCompatibilityError: If pack is incompatible
        """
        # Validate priority
        if priority < 1:
            raise PresetValidationError("Priority must be a positive integer (1 or higher)")

        manifest_path = source_dir / "preset.yml"
        manifest = PresetManifest(manifest_path)

        self.check_compatibility(manifest, speckit_version)

        if self.registry.is_installed(manifest.id):
            raise PresetError(
                f"Preset '{manifest.id}' is already installed. "
                f"Use 'specify preset remove {manifest.id}' first."
            )

        dest_dir = self.presets_dir / manifest.id
        if dest_dir.exists():
            shutil.rmtree(dest_dir)

        shutil.copytree(source_dir, dest_dir)

        # Register command overrides with AI agents
        registered_commands = self._register_commands(manifest, dest_dir)

        # Update corresponding skills when --ai-skills was previously used
        registered_skills = self._register_skills(manifest, dest_dir)

        # Detect wrap commands before registry.add() so a read failure doesn't
        # leave a partially-committed registry entry.
        wrap_commands = []
        try:
            from .agents import CommandRegistrar as _CR
            _registrar = _CR()
            for cmd_tmpl in manifest.templates:
                if cmd_tmpl.get("type") != "command":
                    continue
                cmd_file = dest_dir / cmd_tmpl["file"]
                if not cmd_file.exists():
                    continue
                cmd_fm, _ = _registrar.parse_frontmatter(cmd_file.read_text(encoding="utf-8"))
                if cmd_fm.get("strategy") == "wrap":
                    wrap_commands.append(cmd_tmpl["name"])
        except ImportError:
            pass

        self.registry.add(manifest.id, {
            "version": manifest.version,
            "source": "local",
            "manifest_hash": manifest.get_hash(),
            "enabled": True,
            "priority": priority,
            "registered_commands": registered_commands,
            "registered_skills": registered_skills,
            "wrap_commands": wrap_commands,
        })

        for cmd_name in wrap_commands:
            self._replay_wraps_for_command(cmd_name)

        return manifest