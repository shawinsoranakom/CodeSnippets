async def service_handle(service: ServiceCall) -> None:
        """Handle the applying of a service."""
        master_id = service.data.get("master")
        slaves_ids = service.data.get("slaves")
        all_media_players = [
            entry.runtime_data.media_player
            for entry in hass.config_entries.async_loaded_entries(DOMAIN)
            if entry.runtime_data.media_player is not None
        ]
        slaves = []
        if slaves_ids:
            slaves = [
                media_player
                for media_player in all_media_players
                if media_player.entity_id in slaves_ids
            ]

        master = next(
            iter(
                [
                    media_player
                    for media_player in all_media_players
                    if media_player.entity_id == master_id
                ]
            ),
            None,
        )

        if master is None:
            _LOGGER.warning("Unable to find master with entity_id: %s", str(master_id))
            return

        if service.service == SERVICE_PLAY_EVERYWHERE:
            slaves = [
                media_player
                for media_player in all_media_players
                if media_player.entity_id != master_id
            ]
            await hass.async_add_executor_job(master.create_zone, slaves)
        elif service.service == SERVICE_CREATE_ZONE:
            await hass.async_add_executor_job(master.create_zone, slaves)
        elif service.service == SERVICE_REMOVE_ZONE_SLAVE:
            await hass.async_add_executor_job(master.remove_zone_slave, slaves)
        elif service.service == SERVICE_ADD_ZONE_SLAVE:
            await hass.async_add_executor_job(master.add_zone_slave, slaves)