async def get(
        self,
        request: Request,
        backup_id: str,
    ) -> StreamResponse | FileResponse | Response:
        """Download a backup file."""
        if not request["hass_user"].is_admin:
            return Response(status=HTTPStatus.UNAUTHORIZED)
        try:
            agent_id = request.query.getone("agent_id")
        except KeyError:
            return Response(status=HTTPStatus.BAD_REQUEST)
        try:
            password = request.query.getone("password")
        except KeyError:
            password = None

        hass = request.app[KEY_HASS]
        manager = hass.data[DATA_MANAGER]
        if agent_id not in manager.backup_agents:
            return Response(status=HTTPStatus.BAD_REQUEST)
        agent = manager.backup_agents[agent_id]
        try:
            backup = await agent.async_get_backup(backup_id)
        except BackupNotFound:
            return Response(status=HTTPStatus.NOT_FOUND)

        # Check for None to be backwards compatible with the old BackupAgent API,
        # this can be removed in HA Core 2025.10
        if not backup:
            frame.report_usage(
                "returns None from BackupAgent.async_get_backup",
                breaks_in_ha_version="2025.10",
                integration_domain=agent_id.partition(".")[0],
            )
            return Response(status=HTTPStatus.NOT_FOUND)

        headers = {
            CONTENT_DISPOSITION: f"attachment; filename={slugify(backup.name)}.tar",
            CONTENT_TYPE: "application/x-tar",
        }

        try:
            if not password or not backup.protected:
                return await self._send_backup_no_password(
                    request, headers, backup_id, agent_id, agent, manager
                )
            return await self._send_backup_with_password(
                hass,
                backup,
                request,
                headers,
                backup_id,
                agent_id,
                password,
                agent,
                manager,
            )
        except BackupNotFound:
            return Response(status=HTTPStatus.NOT_FOUND)