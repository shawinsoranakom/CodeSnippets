def __init__(
        self,
        device: Device,
        coordinator: TPLinkDataUpdateCoordinator,
        description: TPLinkEntityDescription,
        *,
        feature: Feature | None = None,
        parent: Device | None = None,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._device: Device = device
        self._parent = parent
        self._feature = feature

        registry_device = device
        device_name = get_device_name(device, parent=parent)
        translation_key: str | None = None
        translation_placeholders: Mapping[str, str] | None = None

        if parent and parent.device_type is not Device.Type.Hub:
            if not feature or feature.id == PRIMARY_STATE_ID:
                # Entity will be added to parent if not a hub and no feature
                # parameter (i.e. core platform like Light, Fan) or the feature
                # is the primary state
                registry_device = parent
                device_name = get_device_name(registry_device)
                if not device_name:
                    translation_key = "unnamed_device"
                    translation_placeholders = {"model": parent.model}
            else:
                # Prefix the device name with the parent name unless it is a
                # hub attached device. Sensible default for child devices like
                # strip plugs or the ks240 where the child alias makes more
                # sense in the context of the parent. i.e. Hall Ceiling Fan &
                # Bedroom Ceiling Fan; Child device aliases will be Ceiling Fan
                # and Dimmer Switch for both so should be distinguished by the
                # parent name.
                parent_device_name = get_device_name(parent)
                child_device_name = get_device_name(device, parent=parent)
                if parent_device_name:
                    device_name = f"{parent_device_name} {child_device_name}"
                else:
                    device_name = None
                    translation_key = "unnamed_device"
                    translation_placeholders = {
                        "model": f"{parent.model} {child_device_name}"
                    }

        if device_name is None and not translation_key:
            translation_key = "unnamed_device"
            translation_placeholders = {"model": device.model}

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(registry_device.device_id))},
            manufacturer="TP-Link",
            model=registry_device.model,
            name=device_name,
            translation_key=translation_key,
            translation_placeholders=translation_placeholders,
            sw_version=registry_device.hw_info["sw_ver"],
            hw_version=registry_device.hw_info["hw_ver"],
        )

        # child device entities will link via_device unless they were created
        # above on the parent. Otherwise the mac connections is set which or
        # for wall switches like the ks240 will mean the child and parent devices
        # are treated as one device.
        if (
            parent is not None
            and parent != registry_device
            and parent.device_type is not Device.Type.WallSwitch
        ):
            self._attr_device_info["via_device"] = (DOMAIN, parent.device_id)
        else:
            self._attr_device_info["connections"] = {
                (dr.CONNECTION_NETWORK_MAC, device.mac)
            }

        self._attr_unique_id = self._get_unique_id()