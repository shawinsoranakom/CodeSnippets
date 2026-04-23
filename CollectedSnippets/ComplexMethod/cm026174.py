async def async_client_leave_group(self, force=False):
        """Make self leave the group.

        Should only be called for clients.
        """
        _LOGGER.debug("%s client leave called", self.entity_id)
        if not force and (
            self.source_id == ATTR_MAIN_SYNC
            or [
                entity
                for entity in self.other_zones
                if entity.source_id == ATTR_MC_LINK
            ]
        ):
            await self.coordinator.musiccast.zone_unjoin(self._zone_id)
        else:
            servers = [
                server
                for server in self.get_all_server_entities()
                if server.coordinator.data.group_id == self.coordinator.data.group_id
            ]
            await self.coordinator.musiccast.mc_client_unjoin()
            if servers:
                await servers[0].coordinator.musiccast.mc_server_group_reduce(
                    servers[0].zone_id, [self.ip_address], self.get_distribution_num()
                )