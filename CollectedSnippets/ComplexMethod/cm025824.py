async def async_can_decrypt_on_download(
        self,
        backup_id: str,
        *,
        agent_id: str,
        password: str | None,
    ) -> None:
        """Check if we are able to decrypt the backup on download."""
        try:
            agent = self.backup_agents[agent_id]
        except KeyError as err:
            raise BackupManagerError(f"Invalid agent selected: {agent_id}") from err
        try:
            backup = await agent.async_get_backup(backup_id)
        except BackupNotFound as err:
            raise BackupManagerError(
                f"Backup {backup_id} not found in agent {agent_id}"
            ) from err
        # Check for None to be backwards compatible with the old BackupAgent API,
        # this can be removed in HA Core 2025.10
        if not backup:
            frame.report_usage(
                "returns None from BackupAgent.async_get_backup",
                breaks_in_ha_version="2025.10",
                integration_domain=agent_id.partition(".")[0],
            )
            raise BackupManagerError(
                f"Backup {backup_id} not found in agent {agent_id}"
            )
        reader: IO[bytes]
        if agent_id in self.local_backup_agents:
            local_agent = self.local_backup_agents[agent_id]
            path = local_agent.get_backup_path(backup_id)
            reader = await self.hass.async_add_executor_job(open, path.as_posix(), "rb")
        else:
            backup_stream = await agent.async_download_backup(backup_id)
            reader = cast(IO[bytes], AsyncIteratorReader(self.hass.loop, backup_stream))
        try:
            await self.hass.async_add_executor_job(
                validate_password_stream, reader, password
            )
        except backup_util.IncorrectPassword as err:
            raise IncorrectPasswordError from err
        except backup_util.UnsupportedSecureTarVersion as err:
            raise DecryptOnDowloadNotSupported from err
        except backup_util.DecryptError as err:
            raise BackupManagerError(str(err)) from err
        finally:
            reader.close()