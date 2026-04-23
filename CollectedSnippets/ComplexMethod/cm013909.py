def _handle_exception(
        self, code: types.CodeType, offset: int, exception: BaseException
    ) -> None:
        """Common exception handling logic."""
        if self._quitting:
            return
        frame = self._find_frame_for_code(code)
        if frame is None:
            return
        state = self._frame_states.get(frame)
        if state is None:
            return

        # If we're waiting for this frame to return, the return was interrupted
        if self._return_from_frame is not None and (
            frame is self._return_from_frame or code is self._return_from_frame.f_code
        ):
            self._return_from_frame = None

        # If we're waiting for next-in-frame, the execution was interrupted
        if self._next_in_frame is not None and (
            frame is self._next_in_frame or code is self._next_in_frame.f_code
        ):
            self._next_in_frame = None
            self._stop_at_new_code = True

        state.current_offset = offset

        inst = state.offset_to_inst.get(offset)
        inst_str = inst.opname if inst else "<unknown>"
        current_index = state.offset_to_index.get(offset, -1)

        print(f"\n=== Exception raised at instruction {current_index}: {inst_str} ===")
        print(f"=== {type(exception).__name__}: {exception} ===")
        self._interactive_prompt(state)