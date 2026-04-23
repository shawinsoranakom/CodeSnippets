def state(self) -> str | None:
        """Return the state of the valve."""
        reports_position = self.reports_position
        if self.is_opening:
            self.__is_last_toggle_direction_open = True
            return ValveState.OPENING
        if self.is_closing:
            self.__is_last_toggle_direction_open = False
            return ValveState.CLOSING
        if reports_position is True:
            if (current_valve_position := self.current_valve_position) is None:
                return None
            position_zero = current_valve_position == 0
            return ValveState.CLOSED if position_zero else ValveState.OPEN
        if (closed := self.is_closed) is None:
            return None
        return ValveState.CLOSED if closed else ValveState.OPEN