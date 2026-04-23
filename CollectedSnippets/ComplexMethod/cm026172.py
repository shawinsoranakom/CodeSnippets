async def async_join_players(self, group_members: list[str]) -> None:
        """Add all clients given in entities to the group of the server.

        Creates a new group if necessary. Used for join service.
        """
        _LOGGER.debug(
            "%s wants to add the following entities %s",
            self.entity_id,
            str(group_members),
        )

        entities = [
            entity
            for entity in self.get_all_mc_entities()
            if entity.entity_id in group_members
        ]

        if self.state == MediaPlayerState.OFF:
            await self.async_turn_on()

        if not self.is_server and self.musiccast_zone_entity.is_server:
            # The MusicCast Distribution Module of this device is already in use. To use it as a server, we first
            # have to unjoin and wait until the servers are updated.
            await self.musiccast_zone_entity.async_server_close_group()
        elif self.musiccast_zone_entity.is_client:
            await self.async_client_leave_group(True)
        # Use existing group id if we are server, generate a new one else.
        group = (
            self.coordinator.data.group_id
            if self.is_server
            else uuid_util.random_uuid_hex().upper()
        )

        ip_addresses = set()
        # First let the clients join
        for client in entities:
            if client != self:
                try:
                    network_join = await client.async_client_join(group, self)
                except MusicCastGroupException:
                    _LOGGER.warning(
                        (
                            "%s is struggling to update its group data. Will retry"
                            " perform the update"
                        ),
                        client.entity_id,
                    )
                    network_join = await client.async_client_join(group, self)

                if network_join:
                    ip_addresses.add(client.ip_address)

        if ip_addresses:
            await self.coordinator.musiccast.mc_server_group_extend(
                self._zone_id,
                list(ip_addresses),
                group,
                self.get_distribution_num(),
            )
        _LOGGER.debug(
            "%s added the following entities %s", self.entity_id, str(entities)
        )
        _LOGGER.debug(
            "%s has now the following musiccast group %s",
            self.entity_id,
            str(self.musiccast_group),
        )

        await self.update_all_mc_entities(True)