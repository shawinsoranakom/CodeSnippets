def _handle_stream_update(self, data: dict[str, Any]) -> None:
        """Update the entity attributes."""

        change = False
        if value := data["data"].get(Signal.FD_WINDOW):
            self.fd = WindowState.get(value) == "Closed"
            change = True
        if value := data["data"].get(Signal.FP_WINDOW):
            self.fp = WindowState.get(value) == "Closed"
            change = True
        if value := data["data"].get(Signal.RD_WINDOW):
            self.rd = WindowState.get(value) == "Closed"
            change = True
        if value := data["data"].get(Signal.RP_WINDOW):
            self.rp = WindowState.get(value) == "Closed"
            change = True

        if not change:
            return

        if False in (self.fd, self.fp, self.rd, self.rp):
            self._attr_is_closed = False
        elif None in (self.fd, self.fp, self.rd, self.rp):
            self._attr_is_closed = None
        else:
            self._attr_is_closed = True

        self.async_write_ha_state()