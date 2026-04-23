async def async_add_entities(
        self,
        new_entities: Iterable[Entity],
        update_before_add: bool = False,
        *,
        config_subentry_id: str | None = None,
    ) -> None:
        """Add entities for a single platform async.

        This method must be run in the event loop.

        :param config_subentry_id: subentry which the entities should be added to
        """
        if config_subentry_id and (
            not self.config_entry
            or config_subentry_id not in self.config_entry.subentries
        ):
            raise HomeAssistantError(
                f"Can't add entities to unknown subentry {config_subentry_id} of config "
                f"entry {self.config_entry.entry_id if self.config_entry else None}"
            )

        entities: list[Entity] = (
            new_entities if type(new_entities) is list else list(new_entities)
        )
        timeout = max(SLOW_ADD_ENTITY_MAX_WAIT * len(entities), SLOW_ADD_MIN_TIMEOUT)
        if update_before_add:
            await self._async_add_and_update_entities(
                entities, timeout, config_subentry_id
            )
        else:
            await self._async_add_entities(entities, timeout, config_subentry_id)

        if (
            (self.config_entry and self.config_entry.pref_disable_polling)
            or self._async_polling_timer is not None
            or not any(
                # Entity may have failed to add or called `add_to_platform_abort`
                # so we check if the entity is in self.entities before
                # checking `entity.should_poll` since `should_poll` may need to
                # check `self.hass` which will be `None` if the entity did not add
                entity.entity_id
                and entity.entity_id in self.entities
                and entity.should_poll
                for entity in entities
            )
        ):
            return

        self._async_polling_timer = self.hass.loop.call_later(
            self.scan_interval_seconds,
            self._async_handle_interval_callback,
        )