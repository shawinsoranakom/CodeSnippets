async def async_step_zeroconf(
        self, discovery_info: ZeroconfServiceInfo
    ) -> ConfigFlowResult:
        """Handle a discovered HomeKit accessory.

        This flow is triggered by the discovery component.
        """
        # Normalize properties from discovery
        # homekit_python has code to do this, but not in a form we can
        # easily use, so do the bare minimum ourselves here instead.
        properties = {
            key.lower(): value for (key, value) in discovery_info.properties.items()
        }

        if ATTR_PROPERTIES_ID not in properties:
            # This can happen if the TXT record is received after the PTR record
            # we will wait for the next update in this case
            _LOGGER.debug(
                (
                    "HomeKit device %s: id not exposed; TXT record may have not yet"
                    " been received"
                ),
                properties,
            )
            return self.async_abort(reason="invalid_properties")

        # The hkid is a unique random number that looks like a pairing code.
        # It changes if a device is factory reset.
        hkid: str = properties[ATTR_PROPERTIES_ID]
        normalized_hkid = normalize_hkid(hkid)
        upper_case_hkid = hkid.upper()
        status_flags = int(properties["sf"])
        paired = not status_flags & 0x01

        # Set unique-id and error out if it's already configured
        existing_entry = await self.async_set_unique_id(
            normalized_hkid, raise_on_progress=False
        )
        updated_ip_port = {
            "AccessoryIP": discovery_info.host,
            "AccessoryIPs": [
                str(ip_addr)
                for ip_addr in discovery_info.ip_addresses
                if not ip_addr.is_link_local and not ip_addr.is_unspecified
            ],
            "AccessoryPort": discovery_info.port,
        }
        # If the device is already paired and known to us we should monitor c#
        # (config_num) for changes. If it changes, we check for new entities
        if paired and upper_case_hkid in self.hass.data.get(KNOWN_DEVICES, {}):
            if existing_entry:
                self.hass.config_entries.async_update_entry(
                    existing_entry, data={**existing_entry.data, **updated_ip_port}
                )
            return self.async_abort(reason="already_configured")

        # If this aiohomekit doesn't support this particular device, ignore it.
        if not domain_supported(discovery_info.name):
            return self.async_abort(reason="ignored_model")

        model = properties["md"]
        name = domain_to_name(discovery_info.name)
        _LOGGER.debug("Discovered device %s (%s - %s)", name, model, upper_case_hkid)

        # Device isn't paired with us or anyone else.
        # But we have a 'complete' config entry for it - that is probably
        # invalid. Remove it automatically if it has an accessory pairing id
        # (which means it was paired with us at some point) and was not
        # ignored by the user.
        if (
            not paired
            and existing_entry
            and (accessory_pairing_id := existing_entry.data.get("AccessoryPairingID"))
        ):
            if self.controller is None:
                await self._async_setup_controller()

            # mypy can't see that self._async_setup_controller() always
            # sets self.controller or throws
            assert self.controller

            pairing = self.controller.load_pairing(
                accessory_pairing_id, dict(existing_entry.data)
            )

            try:
                await pairing.list_accessories_and_characteristics()
            except AuthenticationError:
                _LOGGER.debug(
                    (
                        "%s (%s - %s) is unpaired. Removing invalid pairing for this"
                        " device"
                    ),
                    name,
                    model,
                    hkid,
                )
                await self.hass.config_entries.async_remove(existing_entry.entry_id)
            else:
                _LOGGER.debug(
                    (
                        "%s (%s - %s) claims to be unpaired but isn't. "
                        "It's implementation of HomeKit is defective "
                        "or a zeroconf relay is broadcasting stale data"
                    ),
                    name,
                    model,
                    hkid,
                )
                return self.async_abort(reason="already_paired")

        # Set unique-id and error out if it's already configured
        self._abort_if_unique_id_configured(updates=updated_ip_port)

        self.hkid = normalized_hkid
        self._device_paired = paired
        if self.hass.config_entries.flow.async_has_matching_flow(self):
            raise AbortFlow("already_in_progress")

        if paired:
            # Device is paired but not to us - ignore it
            _LOGGER.debug("HomeKit device %s ignored as already paired", hkid)
            return self.async_abort(reason="already_paired")

        # Devices in HOMEKIT_IGNORE have native local integrations - users
        # should be encouraged to use native integration and not confused
        # by alternative HK API.
        if model in HOMEKIT_IGNORE:
            return self.async_abort(reason="ignored_model")

        # If this is a HomeKit bridge/accessory exported
        # by *this* HA instance ignore it.
        if self._hkid_is_homekit(hkid):
            return self.async_abort(reason="ignored_model")

        self.name = name
        self.model = model
        self.category = Categories(int(properties.get("ci", 0)))

        # We want to show the pairing form - but don't call async_step_pair
        # directly as it has side effects (will ask the device to show a
        # pairing code)
        return self._async_step_pair_show_form()