def update(
        self,
        *,
        agents: dict[str, AgentParametersDict] | UndefinedType = UNDEFINED,
        automatic_backups_configured: bool | UndefinedType = UNDEFINED,
        create_backup: CreateBackupParametersDict | UndefinedType = UNDEFINED,
        retention: RetentionParametersDict | UndefinedType = UNDEFINED,
        schedule: ScheduleParametersDict | UndefinedType = UNDEFINED,
    ) -> None:
        """Update config."""
        if agents is not UNDEFINED:
            for agent_id, agent_config in agents.items():
                agent_retention = agent_config.get("retention")
                if agent_retention is None:
                    new_agent_retention = None
                else:
                    new_agent_retention = AgentRetentionConfig(
                        copies=agent_retention.get("copies"),
                        days=agent_retention.get("days"),
                    )
                if agent_id not in self.data.agents:
                    old_agent_retention = None
                    self.data.agents[agent_id] = AgentConfig(
                        protected=agent_config.get("protected", True),
                        retention=new_agent_retention,
                    )
                else:
                    new_agent_config = self.data.agents[agent_id]
                    old_agent_retention = new_agent_config.retention
                    if "protected" in agent_config:
                        new_agent_config = replace(
                            new_agent_config, protected=agent_config["protected"]
                        )
                    if "retention" in agent_config:
                        new_agent_config = replace(
                            new_agent_config, retention=new_agent_retention
                        )
                    self.data.agents[agent_id] = new_agent_config
                if new_agent_retention != old_agent_retention:
                    # There's a single retention application method
                    # for both global and agent retention settings.
                    self.data.retention.apply(self._manager)
        if automatic_backups_configured is not UNDEFINED:
            self.data.automatic_backups_configured = automatic_backups_configured
        if create_backup is not UNDEFINED:
            self.data.create_backup = replace(self.data.create_backup, **create_backup)
            if "agent_ids" in create_backup:
                check_unavailable_agents(self._hass, self._manager)
        if retention is not UNDEFINED:
            new_retention = RetentionConfig(**retention)
            if new_retention != self.data.retention:
                self.data.retention = new_retention
                self.data.retention.apply(self._manager)
        if schedule is not UNDEFINED:
            new_schedule = BackupSchedule(**schedule)
            if new_schedule.to_dict() != self.data.schedule.to_dict():
                self.data.schedule = new_schedule
                self.data.schedule.apply(self._manager)

        self._manager.store.save()