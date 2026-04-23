def update(self) -> None:
        """Get the latest state from the device."""

        if not self._attr_available:
            self._attr_available = self._setup_projector()

        if not self._attr_available:
            self._force_off()
            return

        try:
            with self.projector() as projector:
                pwstate = projector.get_power()
                if pwstate in ("on", "warm-up"):
                    self._attr_state = MediaPlayerState.ON
                    self._attr_is_volume_muted = projector.get_mute()[1]
                    self._attr_source = format_input_source(*projector.get_input())
                else:
                    self._force_off()
        except KeyError as err:
            if str(err) == "'OK'":
                self._force_off()
            else:
                raise
        except ProjectorError as err:
            if str(err) == "unavailable time":
                self._force_off()
            elif str(err) == ERR_PROJECTOR_UNAVAILABLE:
                self._attr_available = False
            else:
                raise