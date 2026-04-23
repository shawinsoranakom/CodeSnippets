async def async_check_client_list(self):
        """Let the server check if all its clients are still part of his group."""
        if not self.is_server or self.coordinator.data.group_update_lock.locked():
            return

        _LOGGER.debug("%s updates his group members", self.entity_id)
        client_ips_for_removal = [
            expected_client_ip
            for expected_client_ip in self.coordinator.data.group_client_list
            # The client is no longer part of the group. Prepare removal.
            if expected_client_ip
            not in [entity.ip_address for entity in self.musiccast_group]
        ]

        if client_ips_for_removal:
            _LOGGER.debug(
                "%s says good bye to the following members %s",
                self.entity_id,
                str(client_ips_for_removal),
            )
            await self.coordinator.musiccast.mc_server_group_reduce(
                self._zone_id, client_ips_for_removal, self.get_distribution_num()
            )
        if len(self.musiccast_group) < 2:
            # The group is empty, stop distribution.
            await self.async_server_close_group()

        self.async_write_ha_state()