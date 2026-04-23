def _register_commands(
        self,
        manifest: PresetManifest,
        preset_dir: Path
    ) -> Dict[str, List[str]]:
        """Register preset command overrides with all detected AI agents.

        Scans the preset's templates for type "command", reads each command
        file, and writes it to every detected agent directory using the
        CommandRegistrar from the agents module.

        Args:
            manifest: Preset manifest
            preset_dir: Installed preset directory

        Returns:
            Dictionary mapping agent names to lists of registered command names
        """
        command_templates = [
            t for t in manifest.templates if t.get("type") == "command"
        ]
        if not command_templates:
            return {}

        # Filter out extension command overrides if the extension isn't installed.
        # Command names follow the pattern: speckit.<ext-id>.<cmd-name>
        # Core commands (e.g. speckit.specify) have only one dot — always register.
        extensions_dir = self.project_root / ".specify" / "extensions"
        filtered = []
        for cmd in command_templates:
            parts = cmd["name"].split(".")
            if len(parts) >= 3 and parts[0] == "speckit":
                ext_id = parts[1]
                if not (extensions_dir / ext_id).is_dir():
                    continue
            filtered.append(cmd)

        if not filtered:
            return {}

        try:
            from .agents import CommandRegistrar
        except ImportError:
            return {}

        registrar = CommandRegistrar()
        return registrar.register_commands_for_all_agents(
            filtered, manifest.id, preset_dir, self.project_root
        )