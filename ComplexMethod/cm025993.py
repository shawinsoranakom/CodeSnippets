async def transform(
        self,
        hsbk: list[float | int | None],
        kwargs: dict[str, Any] | None = None,
        duration: float = 0,
        rapid: bool = False,
    ) -> None:
        """Transform the bulb color, including per-zone updates."""
        bulb = self.bulb
        color_zones = bulb.color_zones
        num_zones = self.coordinator.get_number_of_zones()
        zone_kwargs = kwargs or {}
        duration_ms = round(duration * 1000)

        # Zone brightness is not reported when powered off
        if not self.is_on and hsbk[HSBK_BRIGHTNESS] is None:
            await self.set_power(True)
            await asyncio.sleep(LIFX_STATE_SETTLE_DELAY)
            await self.update_color_zones()
            await self.set_power(False)

        if (zones := zone_kwargs.get(ATTR_ZONES)) is None:
            # Fast track: setting all zones to the same brightness and color
            # can be treated as a single-zone bulb.
            first_zone = color_zones[0]
            first_zone_brightness = first_zone[HSBK_BRIGHTNESS]
            all_zones_have_same_brightness = all(
                color_zones[zone][HSBK_BRIGHTNESS] == first_zone_brightness
                for zone in range(num_zones)
            )
            all_zones_are_the_same = all(
                color_zones[zone] == first_zone for zone in range(num_zones)
            )
            if (
                all_zones_have_same_brightness or hsbk[HSBK_BRIGHTNESS] is not None
            ) and (all_zones_are_the_same or hsbk[HSBK_KELVIN] is not None):
                await super().transform(
                    hsbk, kwargs=zone_kwargs, duration=duration, rapid=rapid
                )
                return

            zones = list(range(num_zones))
        else:
            zones = [x for x in set(zones) if x < num_zones]

        # Send new color to each zone
        for index, zone in enumerate(zones):
            zone_hsbk = merge_hsbk(color_zones[zone], hsbk)
            apply = 1 if (index == len(zones) - 1) else 0
            try:
                await self.coordinator.async_set_color_zones(
                    zone, zone, zone_hsbk, duration_ms, apply
                )
            except TimeoutError as ex:
                raise HomeAssistantError(
                    f"Timeout setting color zones for {self.name}"
                ) from ex

        # set_color_zones does not update the
        # state of the device, so we need to do that
        await self.get_color()