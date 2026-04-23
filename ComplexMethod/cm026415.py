async def async_flux_update(self, utcnow=None):
        """Update all the lights using flux."""
        if utcnow is None:
            utcnow = dt_utcnow()

        now = as_local(utcnow)

        sunset = get_astral_event_date(self.hass, SUN_EVENT_SUNSET, now.date())
        start_time = self.find_start_time(now)
        stop_time = self.find_stop_time(now)

        if stop_time <= start_time:
            # stop_time does not happen in the same day as start_time
            if start_time < now:
                # stop time is tomorrow
                stop_time += datetime.timedelta(days=1)
        elif now < start_time:
            # stop_time was yesterday since the new start_time is not reached
            stop_time -= datetime.timedelta(days=1)

        if start_time < now < sunset:
            # Daytime
            time_state = "day"
            temp_range = abs(self._start_colortemp - self._sunset_colortemp)
            day_length = int(sunset.timestamp() - start_time.timestamp())
            seconds_from_start = int(now.timestamp() - start_time.timestamp())
            percentage_complete = seconds_from_start / day_length
            temp_offset = temp_range * percentage_complete
            if self._start_colortemp > self._sunset_colortemp:
                temp = self._start_colortemp - temp_offset
            else:
                temp = self._start_colortemp + temp_offset
        else:
            # Night time
            time_state = "night"

            if now < stop_time:
                if stop_time < start_time and stop_time.day == sunset.day:
                    # we need to use yesterday's sunset time
                    sunset_time = sunset - datetime.timedelta(days=1)
                else:
                    sunset_time = sunset

                night_length = int(stop_time.timestamp() - sunset_time.timestamp())
                seconds_from_sunset = int(now.timestamp() - sunset_time.timestamp())
                percentage_complete = seconds_from_sunset / night_length
            else:
                percentage_complete = 1

            temp_range = abs(self._sunset_colortemp - self._stop_colortemp)
            temp_offset = temp_range * percentage_complete
            if self._sunset_colortemp > self._stop_colortemp:
                temp = self._sunset_colortemp - temp_offset
            else:
                temp = self._sunset_colortemp + temp_offset
        rgb = color_temperature_to_rgb(temp)
        x_val, y_val, b_val = color_RGB_to_xy_brightness(*rgb)
        brightness = self._brightness or b_val
        if self._disable_brightness_adjust:
            brightness = None
        if self._mode == MODE_XY:
            await async_set_lights_xy(
                self.hass, self._lights, x_val, y_val, brightness, self._transition
            )
            _LOGGER.debug(
                (
                    "Lights updated to x:%s y:%s brightness:%s, %s%% "
                    "of %s cycle complete at %s"
                ),
                x_val,
                y_val,
                brightness,
                round(percentage_complete * 100),
                time_state,
                now,
            )
        elif self._mode == MODE_RGB:
            await async_set_lights_rgb(self.hass, self._lights, rgb, self._transition)
            _LOGGER.debug(
                "Lights updated to rgb:%s, %s%% of %s cycle complete at %s",
                rgb,
                round(percentage_complete * 100),
                time_state,
                now,
            )
        else:
            await async_set_lights_temp(
                self.hass, self._lights, int(temp), brightness, self._transition
            )
            _LOGGER.debug(
                (
                    "Lights updated to kelvin:%s brightness:%s, %s%% "
                    "of %s cycle complete at %s"
                ),
                temp,
                brightness,
                round(percentage_complete * 100),
                time_state,
                now,
            )