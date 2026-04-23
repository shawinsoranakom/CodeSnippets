def device_name(self, lookup_value: str) -> str | None:
        """Get the device name from an device id, or entity id."""
        device_reg = dr.async_get(self.hass)
        if device := device_reg.async_get(lookup_value):
            return device.name_by_user or device.name

        ent_reg = er.async_get(self.hass)

        try:
            cv.entity_id(lookup_value)
        except vol.Invalid:
            pass
        else:
            if entity := ent_reg.async_get(lookup_value):
                if entity.device_id and (
                    device := device_reg.async_get(entity.device_id)
                ):
                    return device.name_by_user or device.name

        return None