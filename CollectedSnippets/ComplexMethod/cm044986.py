def remove(self, extension_id: str, keep_config: bool = False) -> bool:
        """Remove an installed extension.

        Args:
            extension_id: Extension ID
            keep_config: If True, preserve config files (don't delete extension dir)

        Returns:
            True if extension was removed
        """
        if not self.registry.is_installed(extension_id):
            return False

        # Get registered commands and skills before removal
        metadata = self.registry.get(extension_id)
        registered_commands = metadata.get("registered_commands", {}) if metadata else {}
        raw_skills = metadata.get("registered_skills", []) if metadata else []
        # Normalize: must be a list of plain strings to avoid corrupted-registry errors
        if isinstance(raw_skills, list):
            registered_skills = [s for s in raw_skills if isinstance(s, str)]
        else:
            registered_skills = []

        extension_dir = self.extensions_dir / extension_id

        # Unregister commands from all AI agents
        if registered_commands:
            registrar = CommandRegistrar()
            registrar.unregister_commands(registered_commands, self.project_root)

        # Unregister agent skills
        self._unregister_extension_skills(registered_skills, extension_id)

        if keep_config:
            # Preserve config files, only remove non-config files
            if extension_dir.exists():
                for child in extension_dir.iterdir():
                    # Keep top-level *-config.yml and *-config.local.yml files
                    if child.is_file() and (
                        child.name.endswith("-config.yml") or
                        child.name.endswith("-config.local.yml")
                    ):
                        continue
                    if child.is_dir():
                        shutil.rmtree(child)
                    else:
                        child.unlink()
        else:
            # Backup config files before deleting
            if extension_dir.exists():
                # Use subdirectory per extension to avoid name accumulation
                # (e.g., jira-jira-config.yml on repeated remove/install cycles)
                backup_dir = self.extensions_dir / ".backup" / extension_id
                backup_dir.mkdir(parents=True, exist_ok=True)

                # Backup both primary and local override config files
                config_files = list(extension_dir.glob("*-config.yml")) + list(
                    extension_dir.glob("*-config.local.yml")
                )
                for config_file in config_files:
                    backup_path = backup_dir / config_file.name
                    shutil.copy2(config_file, backup_path)

            # Remove extension directory
            if extension_dir.exists():
                shutil.rmtree(extension_dir)

        # Unregister hooks
        hook_executor = HookExecutor(self.project_root)
        hook_executor.unregister_hooks(extension_id)

        # Update registry
        self.registry.remove(extension_id)

        return True