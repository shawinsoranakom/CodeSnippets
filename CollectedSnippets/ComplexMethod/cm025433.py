def _determine_interval(self) -> int:
        """Calculate new interval between two API fetch (in minutes)."""
        intervals = {"default": self._max_interval}
        for device in self._devices.values():
            # Max interval if no location
            if device.location is None:
                continue

            current_zone = run_callback_threadsafe(
                self.hass.loop,
                async_active_zone,
                self.hass,
                device.location[DEVICE_LOCATION_LATITUDE],
                device.location[DEVICE_LOCATION_LONGITUDE],
                device.location[DEVICE_LOCATION_HORIZONTAL_ACCURACY],
            ).result()

            # Max interval if in zone
            if current_zone is not None:
                continue

            zones = (
                self.hass.states.get(entity_id)
                for entity_id in sorted(self.hass.states.entity_ids("zone"))
            )

            distances = []
            for zone_state in zones:
                if zone_state is None:
                    continue
                zone_state_lat = zone_state.attributes[DEVICE_LOCATION_LATITUDE]
                zone_state_long = zone_state.attributes[DEVICE_LOCATION_LONGITUDE]
                zone_distance = distance(
                    device.location[DEVICE_LOCATION_LATITUDE],
                    device.location[DEVICE_LOCATION_LONGITUDE],
                    zone_state_lat,
                    zone_state_long,
                )
                if zone_distance is not None:
                    distances.append(round(zone_distance / 1000, 1))

            # Max interval if no zone
            if not distances:
                continue
            mindistance = min(distances)

            # Calculate out how long it would take for the device to drive
            # to the nearest zone at 120 km/h:
            interval = round(mindistance / 2)

            # Never poll more than once per minute
            interval = max(interval, 1)

            if interval > 180:
                # Three hour drive?
                # This is far enough that they might be flying
                interval = self._max_interval

            if (
                device.battery_level is not None
                and device.battery_level <= 33
                and mindistance > 3
            ):
                # Low battery - let's check half as often
                interval = interval * 2

            intervals[device.name] = interval

        return max(
            int(min(intervals.items(), key=operator.itemgetter(1))[1]),
            self._max_interval,
        )