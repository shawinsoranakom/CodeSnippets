async def async_update(self) -> None:
        """Update camera entity and refresh attributes."""
        if (
            self._device.has_capability(MOTION_DETECTION_CAPABILITY)
            and self._attr_motion_detection_enabled != self._device.motion_detection
        ):
            self._attr_motion_detection_enabled = self._device.motion_detection
            self.async_write_ha_state()

        if TYPE_CHECKING:
            # _last_event is set before calling update so will never be None
            assert self._last_event

        if self._last_event["recording"]["status"] != "ready":
            return

        utcnow = dt_util.utcnow()
        if self._last_video_id == self._last_event["id"] and utcnow <= self._expires_at:
            return

        if self._last_video_id != self._last_event["id"]:
            self._images = {}

        self._video_url = await self._async_get_video()

        self._last_video_id = self._last_event["id"]
        self._expires_at = FORCE_REFRESH_INTERVAL + utcnow