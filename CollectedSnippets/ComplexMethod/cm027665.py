def area_name(self, lookup_value: str) -> str | None:
        """Get the area name from an area id, device id, or entity id."""
        area_reg = ar.async_get(self.hass)
        if area := area_reg.async_get_area(lookup_value):
            return area.name

        dev_reg = dr.async_get(self.hass)
        ent_reg = er.async_get(self.hass)
        # Import here, not at top-level to avoid circular import
        from homeassistant.helpers import config_validation as cv  # noqa: PLC0415

        try:
            cv.entity_id(lookup_value)
        except vol.Invalid:
            pass
        else:
            if entity := ent_reg.async_get(lookup_value):
                # If entity has an area ID, get the area name for that
                if entity.area_id:
                    return self._get_area_name(area_reg, entity.area_id)
                # If entity has a device ID and the device exists with an area ID, get the
                # area name for that
                if (
                    entity.device_id
                    and (device := dev_reg.async_get(entity.device_id))
                    and device.area_id
                ):
                    return self._get_area_name(area_reg, device.area_id)

        if (device := dev_reg.async_get(lookup_value)) and device.area_id:
            return self._get_area_name(area_reg, device.area_id)

        return None