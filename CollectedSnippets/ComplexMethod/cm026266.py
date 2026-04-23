async def async_update_static_infos(
        self,
        hass: HomeAssistant,
        entry: ESPHomeConfigEntry,
        infos: list[EntityInfo],
        mac: str,
    ) -> None:
        """Distribute an update of static infos to all platforms."""
        # First, load all platforms
        needed_platforms: set[Platform] = set()

        if self.device_info:
            if async_get_dashboard(hass):
                # Only load the update platform if the device_info is set
                # When we restore the entry, the device_info may not be set yet
                # and we don't want to load the update platform since it needs
                # a complete device_info.
                needed_platforms.add(Platform.UPDATE)
            if self.device_info.voice_assistant_feature_flags_compat(self.api_version):
                needed_platforms.add(Platform.BINARY_SENSOR)
                needed_platforms.add(Platform.SELECT)

        # Make a dict of the EntityInfo by type and send
        # them to the listeners for each specific EntityInfo type
        info_types_to_platform = INFO_TYPE_TO_PLATFORM
        infos_by_type: defaultdict[type[EntityInfo], list[EntityInfo]] = defaultdict(
            list
        )
        for info in infos:
            info_type = type(info)
            if platform := info_types_to_platform.get(info_type):
                needed_platforms.add(platform)
                infos_by_type[info_type].append(info)
            else:
                _LOGGER.warning(
                    "Entity type %s is not supported in this version of Home Assistant",
                    info_type,
                )
        await self._ensure_platforms_loaded(hass, entry, needed_platforms)

        for type_, callbacks in self.entity_info_callbacks.items():
            # If all entities for a type are removed, we
            # still need to call the callbacks with an empty list
            # to make sure the entities are removed.
            entity_infos = infos_by_type.get(type_, [])
            for callback_ in callbacks:
                callback_(entity_infos)

        # Finally update static info subscriptions
        for callback_ in self.static_info_update_subscriptions:
            callback_(infos)