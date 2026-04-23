async def async_added_to_hass(self) -> None:
        """Register update callback."""
        await super().async_added_to_hass()
        # Remove temporary bogus entity_id if added
        tmp_entity = TMP_ENTITY.format(self._device_id)
        if (
            tmp_entity
            in self.hass.data[DATA_ENTITY_LOOKUP][EVENT_KEY_COMMAND][self._device_id]
        ):
            self.hass.data[DATA_ENTITY_LOOKUP][EVENT_KEY_COMMAND][
                self._device_id
            ].remove(tmp_entity)

        # Register id and aliases
        self.hass.data[DATA_ENTITY_LOOKUP][EVENT_KEY_COMMAND][self._device_id].append(
            self.entity_id
        )
        if self._group:
            self.hass.data[DATA_ENTITY_GROUP_LOOKUP][EVENT_KEY_COMMAND][
                self._device_id
            ].append(self.entity_id)
        # aliases respond to both normal and group commands (allon/alloff)
        if self._aliases:
            for _id in self._aliases:
                self.hass.data[DATA_ENTITY_LOOKUP][EVENT_KEY_COMMAND][_id].append(
                    self.entity_id
                )
                self.hass.data[DATA_ENTITY_GROUP_LOOKUP][EVENT_KEY_COMMAND][_id].append(
                    self.entity_id
                )
        # group_aliases only respond to group commands (allon/alloff)
        if self._group_aliases:
            for _id in self._group_aliases:
                self.hass.data[DATA_ENTITY_GROUP_LOOKUP][EVENT_KEY_COMMAND][_id].append(
                    self.entity_id
                )
        # nogroup_aliases only respond to normal commands
        if self._nogroup_aliases:
            for _id in self._nogroup_aliases:
                self.hass.data[DATA_ENTITY_LOOKUP][EVENT_KEY_COMMAND][_id].append(
                    self.entity_id
                )
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, SIGNAL_AVAILABILITY, self._availability_callback
            )
        )
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_HANDLE_EVENT.format(self.entity_id),
                self.handle_event_callback,
            )
        )

        # Process the initial event now that the entity is created
        if self._initial_event:
            self.handle_event_callback(self._initial_event)