def _telnet_callback(self, zone: str, event: str, parameter: str) -> None:
        """Process a telnet command callback."""
        # There are multiple checks implemented which reduce unnecessary updates of the ha state machine
        if zone not in (self._receiver.zone, ALL_ZONES):
            return
        if event not in TELNET_EVENTS:
            return
        # Some updates trigger multiple events like one for artist and one for title for one change
        # We skip every event except the last one
        if event == "NSE" and not parameter.startswith("4"):
            return
        if event == "TA" and not parameter.startswith("ANNAME"):
            return
        if event == "HD" and not parameter.startswith("ALBUM"):
            return
        self.async_write_ha_state()