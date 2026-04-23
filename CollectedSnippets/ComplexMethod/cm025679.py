def _async_process_service_update(
        self, async_service_info: AsyncServiceInfo, service_type: str, name: str
    ) -> None:
        """Process a zeroconf update."""
        for listener in self._service_update_listeners:
            listener(async_service_info)
        info = info_from_service(async_service_info)
        if not info:
            # Prevent the browser thread from collapsing
            _LOGGER.debug("Failed to get addresses for device %s", name)
            return
        _LOGGER.debug("Discovered new device %s %s", name, info)
        props: dict[str, str | None] = info.properties

        # Instance ID conflict detection for Home Assistant core
        if service_type == ZEROCONF_TYPE and (
            discovered_instance_id := props.get("uuid")
        ):
            self._async_check_instance_id_conflict(discovered_instance_id, info)

        discovery_key = DiscoveryKey(
            domain=DOMAIN,
            key=(info.type, info.name),
            version=1,
        )
        domain = None

        # If we can handle it as a HomeKit discovery, we do that here.
        if service_type in HOMEKIT_TYPES and (
            homekit_discovery := async_get_homekit_discovery(
                self.homekit_model_lookups, self.homekit_model_matchers, props
            )
        ):
            domain = homekit_discovery.domain
            discovery_flow.async_create_flow(
                self.hass,
                homekit_discovery.domain,
                {"source": config_entries.SOURCE_HOMEKIT},
                info,
                discovery_key=discovery_key,
            )
            # Continue on here as homekit_controller
            # still needs to get updates on devices
            # so it can see when the 'c#' field is updated.
            #
            # We only send updates to homekit_controller
            # if the device is already paired in order to avoid
            # offering a second discovery for the same device
            if not is_homekit_paired(props) and not homekit_discovery.always_discover:
                # If the device is paired with HomeKit we must send on
                # the update to homekit_controller so it can see when
                # the 'c#' field is updated. This is used to detect
                # when the device has been reset or updated.
                #
                # If the device is not paired and we should not always
                # discover it, we can stop here.
                return

        if not (matchers := self.zeroconf_types.get(service_type)):
            return

        # Not all homekit types are currently used for discovery
        # so not all service type exist in zeroconf_types
        for matcher in matchers:
            if len(matcher) > 1:
                if ATTR_NAME in matcher and not _memorized_fnmatch(
                    info.name.lower(), matcher[ATTR_NAME]
                ):
                    continue
                if ATTR_PROPERTIES in matcher and not _match_against_props(
                    matcher[ATTR_PROPERTIES], props
                ):
                    continue

            matcher_domain = matcher[ATTR_DOMAIN]
            # Create a type annotated regular dict since this is a hot path and creating
            # a regular dict is slightly cheaper than calling ConfigFlowContext
            context: config_entries.ConfigFlowContext = {
                "source": config_entries.SOURCE_ZEROCONF,
            }
            if domain:
                # Domain of integration that offers alternative API to handle
                # this device.
                context["alternative_domain"] = domain

            discovery_flow.async_create_flow(
                self.hass,
                matcher_domain,
                context,
                info,
                discovery_key=discovery_key,
            )