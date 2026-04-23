async def async_create_backup(
        self,
        *,
        agent_ids: list[str],
        backup_name: str,
        extra_metadata: dict[str, bool | str],
        include_addons: list[str] | None,
        include_all_addons: bool,
        include_database: bool,
        include_folders: list[Folder] | None,
        include_homeassistant: bool,
        on_progress: Callable[[CreateBackupEvent], None],
        password: str | None,
    ) -> tuple[NewBackup, asyncio.Task[WrittenBackup]]:
        """Create a backup."""
        if not include_homeassistant and include_database:
            raise HomeAssistantError(
                "Cannot create a backup with database but without Home Assistant"
            )
        manager = self._hass.data[DATA_MANAGER]

        include_addons_set: supervisor_backups.AddonSet | set[str] | None = None
        if include_all_addons:
            include_addons_set = supervisor_backups.AddonSet.ALL
        elif include_addons:
            include_addons_set = set(include_addons)
        include_folders_set = {
            supervisor_backups.Folder(folder) for folder in include_folders or []
        }
        # Always include SSL if Home Assistant is included
        if include_homeassistant:
            include_folders_set.add(supervisor_backups.Folder.SSL)

        hassio_agents: list[SupervisorBackupAgent] = [
            cast(SupervisorBackupAgent, manager.backup_agents[agent_id])
            for agent_id in agent_ids
            if manager.backup_agents[agent_id].domain == DOMAIN
        ]

        # Supervisor does not support creating backups spread across multiple
        # locations, where some locations are encrypted and some are not.
        # It's inefficient to let core do all the copying so we want to let
        # supervisor handle as much as possible.
        # Therefore, we split the locations into two lists: encrypted and decrypted.
        # The backup will be created in the first location in the list sent to
        # supervisor, and if that location is not available, the backup will
        # fail.
        # To make it less likely that the backup fails, we prefer to create the
        # backup in the local storage location if included in the list of
        # locations.
        # Hence, we send the list of locations to supervisor in this priority order:
        # 1. The list which has local storage
        # 2. The longest list of locations
        # 3. The list of encrypted locations
        # In any case the remaining locations will be handled by async_upload_backup.
        encrypted_locations: list[str] = []
        decrypted_locations: list[str] = []
        agents_settings = manager.config.data.agents
        for hassio_agent in hassio_agents:
            if password is not None:
                if agent_settings := agents_settings.get(hassio_agent.agent_id):
                    if agent_settings.protected:
                        encrypted_locations.append(hassio_agent.location)
                    else:
                        decrypted_locations.append(hassio_agent.location)
                else:
                    encrypted_locations.append(hassio_agent.location)
            else:
                decrypted_locations.append(hassio_agent.location)
        locations = []
        if LOCATION_LOCAL_STORAGE in decrypted_locations:
            locations = decrypted_locations
            password = None
            # Move local storage to the front of the list
            decrypted_locations.remove(LOCATION_LOCAL_STORAGE)
            decrypted_locations.insert(0, LOCATION_LOCAL_STORAGE)
        elif LOCATION_LOCAL_STORAGE in encrypted_locations:
            locations = encrypted_locations
            # Move local storage to the front of the list
            encrypted_locations.remove(LOCATION_LOCAL_STORAGE)
            encrypted_locations.insert(0, LOCATION_LOCAL_STORAGE)
        _LOGGER.debug("Encrypted locations: %s", encrypted_locations)
        _LOGGER.debug("Decrypted locations: %s", decrypted_locations)
        if not locations and hassio_agents:
            if len(encrypted_locations) >= len(decrypted_locations):
                locations = encrypted_locations
            else:
                locations = decrypted_locations
                password = None
        locations = locations or [LOCATION_CLOUD_BACKUP]

        date = dt_util.now().isoformat()
        extra_metadata = extra_metadata | {"supervisor.backup_request_date": date}
        filename = suggested_filename_from_name_date(backup_name, date)
        try:
            backup = await self._client.backups.partial_backup(
                supervisor_backups.PartialBackupOptions(
                    addons=include_addons_set,
                    folders=include_folders_set,
                    homeassistant=include_homeassistant,
                    name=backup_name,
                    password=password,
                    compressed=True,
                    location=locations,
                    homeassistant_exclude_database=not include_database,
                    background=True,
                    extra=extra_metadata,
                    filename=PurePath(filename),
                )
            )
        except SupervisorError as err:
            raise BackupReaderWriterError(f"Error creating backup: {err}") from err
        backup_task = self._hass.async_create_task(
            self._async_wait_for_backup(
                backup,
                locations,
                on_progress=on_progress,
                remove_after_upload=locations == [LOCATION_CLOUD_BACKUP],
            ),
            name="backup_manager_create_backup",
            eager_start=False,  # To ensure the task is not started before we return
        )

        return (NewBackup(backup_job_id=backup.job_id.hex), backup_task)