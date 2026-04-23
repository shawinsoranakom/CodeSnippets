def _get_toggle_function[**_P, _R](
        self, fns: dict[str, Callable[_P, _R]]
    ) -> Callable[_P, _R]:
        # If we are opening or closing and we support stopping, then we should stop
        if self.supported_features & CoverEntityFeature.STOP and (
            self.is_closing or self.is_opening
        ):
            return fns["stop"]

        # If we are fully closed or in the process of closing, then we should open
        if self.is_closed or self.is_closing:
            return fns["open"]

        # If we are fully open or in the process of opening, then we should close
        if self.current_cover_position == 100 or self.is_opening:
            return fns["close"]

        # We are any of:
        # * fully open but do not report `current_cover_position`
        # * stopped partially open
        # * either opening or closing, but do not report them
        # If we previously reported opening/closing, we should move in the opposite direction.
        # Otherwise, we must assume we are (partially) open and should always close.
        # Note: _cover_is_last_toggle_direction_open will always remain True if we never report opening/closing.
        return (
            fns["close"] if self._cover_is_last_toggle_direction_open else fns["open"]
        )