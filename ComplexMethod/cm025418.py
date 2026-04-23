async def async_join_players(self, group_members: list[str]) -> None:
        """Add `group_members` to this client's current group."""
        if self._current_group is None:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="join_players_no_group",
                translation_placeholders={
                    "entity_id": self.entity_id,
                },
            )

        # Get the client entity for each group member excluding self
        entity_registry = er.async_get(self.hass)
        clients = [
            entity
            for entity_id in group_members
            if (entity := entity_registry.async_get(entity_id))
            and entity.unique_id != self.unique_id
        ]

        # Get unique ID prefix for this host
        unique_id_prefix = self.get_unique_id(self.coordinator.host_id, "")
        for client in clients:
            # Validate entity is a snapcast client
            if not client.unique_id.startswith(CLIENT_PREFIX):
                raise ServiceValidationError(
                    f"Entity '{client.entity_id}' is not a Snapcast client device."
                )

            # Validate client belongs to the same server
            if not client.unique_id.startswith(unique_id_prefix):
                raise ServiceValidationError(
                    f"Entity '{client.entity_id}' does not belong to the same Snapcast server."
                )

            # Extract client ID and join it to the current group
            identifier = client.unique_id.removeprefix(unique_id_prefix)
            try:
                await self._current_group.add_client(identifier)
            except KeyError as e:
                raise ServiceValidationError(
                    f"Client with identifier '{identifier}' does not exist on the server."
                ) from e

        self.async_write_ha_state()