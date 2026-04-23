async def async_client_join(self, group_id, server) -> bool:
        """Let the client join a group.

        If this client is a server, the server will stop distributing.
        If the client is part of a different group,
        it will leave that group first. Returns True, if the server has to
        add the client on his side.
        """
        # If we should join the group, which is served by the main zone,
        # we can simply select main_sync as input.
        _LOGGER.debug("%s called service client join", self.entity_id)
        if self.state == MediaPlayerState.OFF:
            await self.async_turn_on()
        if self.ip_address == server.ip_address:
            if server.zone == DEFAULT_ZONE:
                await self.async_select_source(ATTR_MAIN_SYNC)
                server.async_write_ha_state()
                return False

            # It is not possible to join a group hosted by zone2 from main zone.
            raise HomeAssistantError(
                "Can not join a zone other than main of the same device."
            )

        if self.musiccast_zone_entity.is_server:
            # If one of the zones of the device is a server, we need to unjoin first.
            _LOGGER.debug(
                (
                    "%s is a server of a group and has to stop distribution "
                    "to use MusicCast for %s"
                ),
                self.musiccast_zone_entity.entity_id,
                self.entity_id,
            )
            await self.musiccast_zone_entity.async_server_close_group()

        elif self.is_client:
            if self.is_part_of_group(server):
                _LOGGER.warning("%s is already part of the group", self.entity_id)
                return False

            _LOGGER.debug(
                "%s is client in a different group, will unjoin first",
                self.entity_id,
            )
            await self.async_client_leave_group()

        elif (
            self.ip_address in server.coordinator.data.group_client_list
            and self.coordinator.data.group_id == server.coordinator.data.group_id
            and self.coordinator.data.group_role == "client"
        ):
            # The device is already part of this group (e.g. main zone is also a client of this group).
            # Just select mc_link as source
            await self.coordinator.musiccast.zone_join(self._zone_id)
            return False

        _LOGGER.debug("%s will now join as a client", self.entity_id)
        await self.coordinator.musiccast.mc_client_join(
            server.ip_address, group_id, self._zone_id
        )
        return True