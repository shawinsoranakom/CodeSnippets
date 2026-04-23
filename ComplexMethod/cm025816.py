async def _async_reload_backup_agents(self, domain: str) -> None:
        """Add backup agent platform to the backup manager."""
        platform = self.backup_agent_platforms[domain]

        # Remove all agents for the domain
        for agent_id in list(self.backup_agents):
            if self.backup_agents[agent_id].domain == domain:
                del self.backup_agents[agent_id]
        for agent_id in list(self.local_backup_agents):
            if self.local_backup_agents[agent_id].domain == domain:
                del self.local_backup_agents[agent_id]

        # Add new agents
        agents = await platform.async_get_backup_agents(self.hass)
        self.backup_agents.update({agent.agent_id: agent for agent in agents})
        self.local_backup_agents.update(
            {
                agent.agent_id: agent
                for agent in agents
                if isinstance(agent, LocalBackupAgent)
            }
        )

        @callback
        def check_unavailable_agents_after_start(hass: HomeAssistant) -> None:
            """Check unavailable agents after start."""
            check_unavailable_agents(hass, self)

        start.async_at_started(self.hass, check_unavailable_agents_after_start)