def from_dict(cls, data: StoredBackupConfig) -> Self:
        """Initialize backup config data from a dict."""
        include_folders_data = data["create_backup"]["include_folders"]
        if include_folders_data:
            include_folders = [Folder(folder) for folder in include_folders_data]
        else:
            include_folders = None
        retention = data["retention"]

        if last_attempted_str := data["last_attempted_automatic_backup"]:
            last_attempted = dt_util.parse_datetime(last_attempted_str)
        else:
            last_attempted = None

        if last_attempted_str := data["last_completed_automatic_backup"]:
            last_completed = dt_util.parse_datetime(last_attempted_str)
        else:
            last_completed = None

        if time_str := data["schedule"]["time"]:
            time = dt_util.parse_time(time_str)
        else:
            time = None
        days = [Day(day) for day in data["schedule"]["days"]]
        agents = {}
        for agent_id, agent_data in data["agents"].items():
            protected = agent_data["protected"]
            stored_retention = agent_data["retention"]
            agent_retention: AgentRetentionConfig | None
            if stored_retention:
                agent_retention = AgentRetentionConfig(
                    copies=stored_retention["copies"],
                    days=stored_retention["days"],
                )
            else:
                agent_retention = None
            agent_config = AgentConfig(
                protected=protected,
                retention=agent_retention,
            )
            agents[agent_id] = agent_config

        return cls(
            agents=agents,
            automatic_backups_configured=data["automatic_backups_configured"],
            create_backup=CreateBackupConfig(
                agent_ids=data["create_backup"]["agent_ids"],
                include_addons=data["create_backup"]["include_addons"],
                include_all_addons=data["create_backup"]["include_all_addons"],
                include_database=data["create_backup"]["include_database"],
                include_folders=include_folders,
                name=data["create_backup"]["name"],
                password=data["create_backup"]["password"],
            ),
            last_attempted_automatic_backup=last_attempted,
            last_completed_automatic_backup=last_completed,
            retention=RetentionConfig(
                copies=retention["copies"],
                days=retention["days"],
            ),
            schedule=BackupSchedule(
                days=days,
                recurrence=ScheduleRecurrence(data["schedule"]["recurrence"]),
                time=time,
            ),
        )