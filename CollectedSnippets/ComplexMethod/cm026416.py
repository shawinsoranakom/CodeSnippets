async def async_set_fan_speed(self, fan_speed: str, **kwargs: Any) -> None:
        """Set fan speed."""
        try:
            split = fan_speed.split("-", 1)
            behavior = split[0]
            spray = int(split[1])
            if behavior.capitalize() in BRAAVA_MOP_BEHAVIORS:
                behavior = behavior.capitalize()
        except IndexError:
            _LOGGER.error(
                "Fan speed error: expected {behavior}-{spray_amount}, got '%s'",
                fan_speed,
            )
            return
        except ValueError:
            _LOGGER.error("Spray amount error: expected integer, got '%s'", split[1])
            return
        if behavior not in BRAAVA_MOP_BEHAVIORS:
            _LOGGER.error(
                "Mop behavior error: expected one of %s, got '%s'",
                str(BRAAVA_MOP_BEHAVIORS),
                behavior,
            )
            return
        if spray not in BRAAVA_SPRAY_AMOUNT:
            _LOGGER.error(
                "Spray amount error: expected one of %s, got '%d'",
                str(BRAAVA_SPRAY_AMOUNT),
                spray,
            )
            return

        overlap = 0
        if behavior == MOP_STANDARD:
            overlap = OVERLAP_STANDARD
        elif behavior == MOP_DEEP:
            overlap = OVERLAP_DEEP
        else:
            overlap = OVERLAP_EXTENDED
        await self.hass.async_add_executor_job(
            self.vacuum.set_preference, "rankOverlap", overlap
        )
        await self.hass.async_add_executor_job(
            self.vacuum.set_preference,
            "padWetness",
            {"disposable": spray, "reusable": spray},
        )