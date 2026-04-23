def _handle_return(
        self, code: types.CodeType, retval: object, frame: types.FrameType | None = None
    ) -> None:
        """Common return handling logic."""
        if self._quitting:
            return
        print(f"\n=== {code.co_name} returned: {retval!r} ===")

        # For sys.monitoring, we don't get the frame directly, but since
        # the frame that's currently returning is the one whose PY_RETURN just
        # fired, code identity is sufficient to match.
        if self._return_from_frame is not None and (
            frame is self._return_from_frame
            or (frame is None and code is self._return_from_frame.f_code)
        ):
            self._return_from_frame = None
            self._stop_after_return = True
            if _HAS_SYS_MONITORING:
                sys.monitoring.restart_events()
        if self._next_in_frame is not None and (
            frame is self._next_in_frame
            or (frame is None and code is self._next_in_frame.f_code)
        ):
            self._next_in_frame = None
            self._stop_after_return = True
            if _HAS_SYS_MONITORING:
                sys.monitoring.restart_events()

        # Clean up frame state to avoid holding dead frame references
        if frame is not None:
            self._frame_states.pop(frame, None)
        else:
            # sys.monitoring path: find and remove matching frame state by code
            for f, s in list(self._frame_states.items()):
                if s.code is code:
                    self._frame_states.pop(f, None)
                    break