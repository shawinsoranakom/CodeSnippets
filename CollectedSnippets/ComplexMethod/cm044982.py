def _get_installed_command_name_map(
        self,
        exclude_extension_id: Optional[str] = None,
    ) -> Dict[str, str]:
        """Return registered command and alias names for installed extensions."""
        installed_names: Dict[str, str] = {}

        for ext_id in self.registry.keys():
            if ext_id == exclude_extension_id:
                continue

            manifest = self.get_extension(ext_id)
            if manifest is None:
                continue

            for cmd in manifest.commands:
                cmd_name = cmd.get("name")
                if isinstance(cmd_name, str):
                    installed_names.setdefault(cmd_name, ext_id)

                aliases = cmd.get("aliases", [])
                if not isinstance(aliases, list):
                    continue

                for alias in aliases:
                    if isinstance(alias, str):
                        installed_names.setdefault(alias, ext_id)

        return installed_names