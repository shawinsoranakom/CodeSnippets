def get_cover_state(self) -> CoverState:
        """Return a CoverState enum representing the state of the cover."""
        set_req = self.gateway.const.SetReq
        v_up = self._values.get(set_req.V_UP) == STATE_ON
        v_down = self._values.get(set_req.V_DOWN) == STATE_ON
        v_stop = self._values.get(set_req.V_STOP) == STATE_ON

        # If a V_DIMMER or V_PERCENTAGE is available, that is the amount
        # the cover is open. Otherwise, use 0 or 100 based on the V_LIGHT
        # or V_STATUS.
        amount = 100
        if set_req.V_DIMMER in self._values:
            amount = self._values[set_req.V_DIMMER]
        else:
            amount = 100 if self._values.get(set_req.V_LIGHT) == STATE_ON else 0

        if amount == 0:
            return CoverState.CLOSED
        if v_up and not v_down and not v_stop:
            return CoverState.OPENING
        if not v_up and v_down and not v_stop:
            return CoverState.CLOSING
        return CoverState.OPEN