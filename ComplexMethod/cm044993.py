def register_hooks(self, manifest: ExtensionManifest):
        """Register extension hooks in project config.

        Args:
            manifest: Extension manifest with hooks to register
        """
        if not hasattr(manifest, "hooks") or not manifest.hooks:
            return

        config = self.get_project_config()

        # Ensure hooks dict exists
        if "hooks" not in config:
            config["hooks"] = {}

        # Register each hook
        for hook_name, hook_config in manifest.hooks.items():
            if hook_name not in config["hooks"]:
                config["hooks"][hook_name] = []

            # Add hook entry
            hook_entry = {
                "extension": manifest.id,
                "command": hook_config.get("command"),
                "enabled": True,
                "optional": hook_config.get("optional", True),
                "prompt": hook_config.get(
                    "prompt", f"Execute {hook_config.get('command')}?"
                ),
                "description": hook_config.get("description", ""),
                "condition": hook_config.get("condition"),
            }

            # Check if already registered
            existing = [
                h
                for h in config["hooks"][hook_name]
                if h.get("extension") == manifest.id
            ]

            if not existing:
                config["hooks"][hook_name].append(hook_entry)
            else:
                # Update existing
                for i, h in enumerate(config["hooks"][hook_name]):
                    if h.get("extension") == manifest.id:
                        config["hooks"][hook_name][i] = hook_entry

        self.save_project_config(config)