def is_on(self) -> bool:
        """Return true if safety issue detected."""
        if super().is_on:
            # parent is on
            return True

        if (
            self._device.powerMainsFailure
            or self._device.moistureDetected
            or self._device.waterlevelDetected
            or self._device.lowBat
            or self._device.dutyCycle
        ):
            return True

        if (
            self._device.smokeDetectorAlarmType is not None
            and self._device.smokeDetectorAlarmType != SmokeDetectorAlarmType.IDLE_OFF
        ):
            return True

        return False