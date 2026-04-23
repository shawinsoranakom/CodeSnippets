def _async_write_ha_state(self) -> None:
        """Write the state to the state machine."""
        # The check for self.platform guards against integrations not using an
        # EntityComponent (which has not been allowed since HA Core 2024.1)
        if not self.platform:
            if self._platform_state is EntityPlatformState.REMOVED:
                # Don't write state if the entity is not added to the platform.
                return
        elif self._platform_state is not EntityPlatformState.ADDED:
            if (entry := self.registry_entry) and entry.disabled_by:
                if not self._disabled_reported:
                    self._disabled_reported = True
                    _LOGGER.warning(
                        (
                            "Entity %s is incorrectly being triggered for updates while it"
                            " is disabled. This is a bug in the %s integration"
                        ),
                        self.entity_id,
                        self.platform.platform_name,
                    )
            return

        state_calculate_start = timer()
        (
            state,
            attr,
            original_name,
            capabilities,
            original_device_class,
            supported_features,
        ) = self.__async_calculate_state()
        time_now = timer()

        if entry := self.registry_entry:
            # Make sure capabilities and other data in the entity registry are up to date.
            # Capabilities include capability attributes, device class and supported features.
            supported_features = supported_features or 0
            if (
                capabilities != entry.capabilities
                or original_device_class != entry.original_device_class
                or supported_features != entry.supported_features
                or original_name != entry.original_name
            ):
                if not self.__capabilities_updated_at_reported:
                    # _Entity__capabilities_updated_at is because of name mangling
                    if not (
                        capabilities_updated_at := getattr(
                            self, "_Entity__capabilities_updated_at", None
                        )
                    ):
                        self.__capabilities_updated_at = deque(
                            maxlen=CAPABILITIES_UPDATE_LIMIT + 1
                        )
                        capabilities_updated_at = self.__capabilities_updated_at
                    capabilities_updated_at.append(time_now)
                    while time_now - capabilities_updated_at[0] > 3600:
                        capabilities_updated_at.popleft()
                    if len(capabilities_updated_at) > CAPABILITIES_UPDATE_LIMIT:
                        self.__capabilities_updated_at_reported = True
                        report_issue = self._suggest_report_issue()
                        _LOGGER.warning(
                            (
                                "Entity %s (%s) is updating its capabilities too often,"
                                " please %s"
                            ),
                            self.entity_id,
                            type(self),
                            report_issue,
                        )
                entity_registry = er.async_get(self.hass)
                self.registry_entry = entity_registry.async_update_entity(
                    self.entity_id,
                    capabilities=capabilities,
                    original_device_class=original_device_class,
                    original_name=original_name,
                    supported_features=supported_features,
                )

        if time_now - state_calculate_start > 0.4 and not self._slow_reported:
            self._slow_reported = True
            report_issue = self._suggest_report_issue()
            _LOGGER.warning(
                "Updating state for %s (%s) took %.3f seconds. Please %s",
                self.entity_id,
                type(self),
                time_now - state_calculate_start,
                report_issue,
            )

        try:
            # Most of the time this will already be
            # set and since try is near zero cost
            # on py3.11+ its faster to assume it is
            # set and catch the exception if it is not.
            custom = self.hass.data[DATA_CUSTOMIZE].get(self.entity_id)
        except KeyError:
            pass
        else:
            # Overwrite properties that have been set in the config file.
            if custom:
                attr |= custom

        if (
            self._context_set is not None
            and time_now - self._context_set > CONTEXT_RECENT_TIME_SECONDS
        ):
            self._context = None
            self._context_set = None

        # Intentionally called with positional args for performance reasons
        self.hass.states.async_set_internal(
            self.entity_id,
            state,
            attr,
            self.force_update,
            self._context,
            self._state_info,
            time_now,
        )