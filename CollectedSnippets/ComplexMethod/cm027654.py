def __async_calculate_state(
        self,
    ) -> tuple[
        str,
        dict[str, Any],
        str | None,
        Mapping[str, Any] | None,
        str | None,
        int | None,
    ]:
        """Calculate state string and attribute mapping.

        Returns a tuple:
        state - the stringified state
        attr - the attribute dictionary
        original_name - the original name which may be overridden
        capability_attr - a mapping with capability attributes
        original_device_class - the device class which may be overridden
        supported_features - the supported features

        This method is called when writing the state to avoid the overhead of creating
        a dataclass object.
        """
        entry = self.registry_entry

        capability_attr = self.capability_attributes
        if self.__group is not None:
            capability_attr = capability_attr.copy() if capability_attr else {}
            capability_attr[ATTR_GROUP_ENTITIES] = self.__group.member_entity_ids.copy()

        attr = capability_attr.copy() if capability_attr else {}

        available = self.available  # only call self.available once per update cycle
        state = self._stringify_state(available)
        if available:
            if state_attributes := self.state_attributes:
                attr |= state_attributes
            if extra_state_attributes := self.extra_state_attributes:
                attr |= extra_state_attributes

        if (unit_of_measurement := self.unit_of_measurement) is not None:
            attr[ATTR_UNIT_OF_MEASUREMENT] = unit_of_measurement

        if assumed_state := self.assumed_state:
            attr[ATTR_ASSUMED_STATE] = assumed_state

        if (attribution := self.attribution) is not None:
            attr[ATTR_ATTRIBUTION] = attribution

        original_device_class = self.device_class
        if (
            device_class := (entry and entry.device_class) or original_device_class
        ) is not None:
            attr[ATTR_DEVICE_CLASS] = str(device_class)

        if (entity_picture := self.entity_picture) is not None:
            attr[ATTR_ENTITY_PICTURE] = entity_picture

        if (icon := (entry and entry.icon) or self.icon) is not None:
            attr[ATTR_ICON] = icon

        original_name = self.name
        if original_name is UNDEFINED:
            original_name = None

        # Use cached friendly name if available and original_name hasn't changed.
        # Cache is invalidated on relevant registry changes.
        if (cached := self._cached_friendly_name) is not None and (
            cached[0] == original_name
        ):
            name = cached[1]
        else:
            if entry is None:
                name = original_name
            else:
                name = er.async_get_full_entity_name(
                    self.hass, entry, original_name=original_name
                )
            self._cached_friendly_name = (original_name, name)

        if name:
            attr[ATTR_FRIENDLY_NAME] = name

        if (supported_features := self.supported_features) is not None:
            attr[ATTR_SUPPORTED_FEATURES] = supported_features

        return (
            state,
            attr,
            original_name,
            capability_attr,
            original_device_class,
            supported_features,
        )