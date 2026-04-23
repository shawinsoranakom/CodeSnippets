def sync_serialize(self, agent_user_id, instance_uuid):
        """Serialize entity for a SYNC response.

        https://developers.google.com/actions/smarthome/create-app#actiondevicessync
        """
        state = self.state
        traits = self.traits()
        entity_config = self.config.entity_config.get(state.entity_id, {})

        # Find entity/device/area registry entries
        entity_entry, device_entry, area_entry = _get_registry_entries(
            self.hass, self.entity_id
        )

        # Build the device info
        device = {
            "id": state.entity_id,
            "attributes": {},
            "traits": [trait.name for trait in traits],
            "willReportState": self.config.should_report_state,
            "type": get_google_type(
                state.domain, state.attributes.get(ATTR_DEVICE_CLASS)
            ),
        }
        # Add name and aliases.
        # The entity's alias list is ordered: the first slot naturally serves
        # as the primary name (set to the auto-generated full entity name by
        # default), while the rest serve as alternative names (nicknames).
        aliases = intent.async_get_entity_aliases(
            self.hass, entity_entry, state=state, allow_empty=False
        )
        name, *aliases = aliases
        name = entity_config.get(CONF_NAME) or name
        device["name"] = {"name": name}
        if (config_aliases := entity_config.get(CONF_ALIASES, [])) or aliases:
            device["name"]["nicknames"] = [name, *config_aliases, *aliases]

        # Add local SDK info if enabled
        if self.config.is_local_sdk_active and self.should_expose_local():
            device["otherDeviceIds"] = [{"deviceId": self.entity_id}]
            device["customData"] = {
                "webhookId": self.config.get_local_webhook_id(agent_user_id),
                "httpPort": URL(get_url(self.hass, allow_external=False)).port,
                "uuid": instance_uuid,
            }

        # Add trait sync attributes
        for trt in traits:
            device["attributes"].update(trt.sync_attributes())

        # Add trait options
        for trt in traits:
            device.update(trt.sync_options())

        # Add roomhint
        if room := entity_config.get(CONF_ROOM_HINT):
            device["roomHint"] = room
        elif area_entry and area_entry.name:
            device["roomHint"] = area_entry.name

        if not device_entry:
            return device

        # Add Matter info
        if "matter" in self.hass.config.components and any(
            x for x in device_entry.identifiers if x[0] == "matter"
        ):
            from homeassistant.components.matter import (  # noqa: PLC0415
                get_matter_device_info,
            )

            # Import matter can block the event loop for multiple seconds
            # so we import it here to avoid blocking the event loop during
            # setup since google_assistant is imported from cloud.
            if matter_info := get_matter_device_info(self.hass, device_entry.id):
                device["matterUniqueId"] = matter_info["unique_id"]
                device["matterOriginalVendorId"] = matter_info["vendor_id"]
                device["matterOriginalProductId"] = matter_info["product_id"]

        # Add deviceInfo
        device_info = {}

        if device_entry.manufacturer:
            device_info["manufacturer"] = device_entry.manufacturer
        if device_entry.model:
            device_info["model"] = device_entry.model
        if device_entry.sw_version:
            device_info["swVersion"] = device_entry.sw_version

        if device_info:
            device["deviceInfo"] = device_info

        return device