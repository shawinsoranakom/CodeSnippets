def remove(self, pack_id: str) -> bool:
        """Remove an installed preset.

        Args:
            pack_id: Preset ID

        Returns:
            True if pack was removed
        """
        if not self.registry.is_installed(pack_id):
            return False

        metadata = self.registry.get(pack_id)
        # Restore original skills when preset is removed
        registered_skills = metadata.get("registered_skills", []) if metadata else []
        registered_commands = metadata.get("registered_commands", {}) if metadata else {}
        wrap_commands = metadata.get("wrap_commands", []) if metadata else []
        pack_dir = self.presets_dir / pack_id

        # _unregister_skills must run before directory deletion (reads preset files)
        if registered_skills:
            self._unregister_skills(registered_skills, pack_dir)
            # When _unregister_skills has already handled skill-agent files, strip
            # those entries from registered_commands to avoid double-deletion.
            # (When registered_skills is empty, skill-agent entries in
            # registered_commands are the only deletion path for those files.)
            try:
                from .agents import CommandRegistrar
            except ImportError:
                CommandRegistrar = None
            if CommandRegistrar is not None:
                registered_commands = {
                    agent_name: cmd_names
                    for agent_name, cmd_names in registered_commands.items()
                    if CommandRegistrar.AGENT_CONFIGS.get(agent_name, {}).get("extension") != "/SKILL.md"
                }

        # Delete the preset directory before mutating the registry so a
        # filesystem failure cannot leave files on disk without a registry entry.
        if pack_dir.exists():
            shutil.rmtree(pack_dir)

        # Remove from registry before replaying so _replay_wraps_for_command sees
        # the post-removal registry state.
        self.registry.remove(pack_id)

        # Separate wrap commands from non-wrap commands in registered_commands.
        non_wrap_commands = {
            agent_name: [c for c in cmd_names if c not in wrap_commands]
            for agent_name, cmd_names in registered_commands.items()
        }
        non_wrap_commands = {k: v for k, v in non_wrap_commands.items() if v}

        # Unregister non-wrap command files from AI agents.
        if non_wrap_commands:
            self._unregister_commands(non_wrap_commands)

        # For each wrapped command, either re-compose remaining wraps or delete.
        for cmd_name in wrap_commands:
            remaining = [
                pid for pid, meta in self.registry.list().items()
                if cmd_name in meta.get("wrap_commands", [])
            ]
            if remaining:
                self._replay_wraps_for_command(cmd_name)
            else:
                # No wrap presets remain — delete the agent file entirely.
                wrap_agent_commands = {
                    agent_name: [c for c in cmd_names if c == cmd_name]
                    for agent_name, cmd_names in registered_commands.items()
                }
                wrap_agent_commands = {k: v for k, v in wrap_agent_commands.items() if v}
                if wrap_agent_commands:
                    self._unregister_commands(wrap_agent_commands)

        return True