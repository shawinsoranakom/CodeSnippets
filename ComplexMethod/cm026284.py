def _async_get_camera(self, data: ProtectData, camera_id: str) -> Camera | None:
        if (camera := data.api.bootstrap.cameras.get(camera_id)) is not None:
            return camera

        entity_registry = er.async_get(self.hass)
        device_registry = dr.async_get(self.hass)

        if (entity := entity_registry.async_get(camera_id)) is None or (
            device := device_registry.async_get(entity.device_id or "")
        ) is None:
            return None

        macs = [c[1] for c in device.connections if c[0] == dr.CONNECTION_NETWORK_MAC]
        for mac in macs:
            if (ufp_device := data.api.bootstrap.get_device_from_mac(mac)) is not None:
                if isinstance(ufp_device, Camera):
                    camera = ufp_device
                    break
        return camera