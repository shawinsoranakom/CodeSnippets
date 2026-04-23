def _handle_instruction(
        self, code: types.CodeType, offset: int, frame: types.FrameType | None = None
    ) -> None:
        """Common instruction handling logic for both tracing backends."""
        if frame is None:
            frame = self._find_frame_for_code(code)
            assert frame is not None
        state = self._get_or_create_frame_state(code, frame)

        # Update stack depth based on the previous instruction's effect.
        # The callback is called BEFORE instruction at 'offset' executes,
        # so we need to apply the effect of the previous instruction first.
        previous_offset = state.current_offset
        if previous_offset >= 0:
            prev_inst = state.offset_to_inst.get(previous_offset)
            if prev_inst is not None:
                # Detect if a jump was taken: current offset != sequential next
                prev_index = state.offset_to_index.get(previous_offset, -1)
                expected_next_index = prev_index + 1
                current_index = state.offset_to_index.get(offset, -1)
                did_jump = current_index != expected_next_index

                try:
                    effect = dis.stack_effect(
                        prev_inst.opcode, prev_inst.arg, jump=did_jump
                    )
                    state.current_stack_depth += effect
                    if state.current_stack_depth < 0:
                        raise RuntimeError(
                            f"Stack depth went negative after {prev_inst.opname} "
                            f"at offset {previous_offset}: depth={state.current_stack_depth}"
                        )
                except (ValueError, TypeError):
                    pass

        state.current_offset = offset
        state.list_index = None  # Reset list position when stepping

        # After 'r' command completes, resume stepping at the next instruction
        if self._stop_after_return:
            self._stop_after_return = False
            state.step_mode = True
            state.step_count = 0
            self._stop_at_new_code = True

        # After 'n', resume stepping when we reach that frame
        if self._next_in_frame is not None and frame is self._next_in_frame:
            if self._next_count > 0:
                # More steps remaining — re-arm for the next instruction in this frame
                self._next_count -= 1
            else:
                self._next_in_frame = None
                state.step_mode = True
                state.step_count = 0
                self._stop_at_new_code = True
            if _HAS_SYS_MONITORING:
                sys.monitoring.restart_events()

        # First instruction - print header and enter step mode (unless suppressed)
        if not state.first_instruction_seen:
            state.first_instruction_seen = True
            if not self._stop_at_new_code:
                state.step_mode = False
            if state.step_mode:
                print(f"\n=== Entering Dynamo-generated code: {code.co_name} ===")
                self._print_help()
            elif self._verbose:
                print(f"\n=== Entering Dynamo-generated code: {code.co_name} ===")

        # Verbose mode: print each instruction before executing (for segfault debugging)
        if self._verbose:
            inst = state.offset_to_inst.get(offset)
            if inst:
                idx = state.offset_to_index.get(offset, -1)
                arg_str = f" {inst.argval}" if inst.arg is not None else ""
                print(f"Running [{idx}] {inst.opname}{arg_str}", flush=True)

        inst = state.offset_to_inst.get(offset)

        # Check if current instruction has a breakpoint (by index)
        current_index = state.offset_to_index.get(offset, -1)
        hit_breakpoint = current_index in state.breakpoints

        # 'r' command: stop at RETURN_VALUE/RETURN_CONST in the target frame
        # so the user can inspect the return value on the stack before returning.
        hit_return_target = False
        if self._return_from_frame is not None and frame is self._return_from_frame:
            if inst is not None and inst.opname in ("RETURN_VALUE", "RETURN_CONST"):
                self._return_from_frame = None
                # After stepping past the return, stop in the caller
                self._stop_after_return = True
                hit_return_target = True

        # Check if we should stop
        # If step_count > 0, we're in the middle of "N s" and should continue
        if state.step_count > 0:
            state.step_count -= 1
            # But still stop for breakpoints and return targets
            if hit_breakpoint or hit_return_target:
                state.step_count = 0  # Cancel remaining steps
            else:
                return  # Continue without prompting

        should_stop = state.step_mode or hit_breakpoint or hit_return_target
        if should_stop:
            if hit_breakpoint:
                if inst is not None and self.is_programmatic_breakpoint(inst):
                    print("Breakpoint hit (programmatic)")
                else:
                    print(f"Breakpoint hit at instruction {current_index}")
            elif hit_return_target:
                print(f"About to return from {code.co_name}")
            self._interactive_prompt(state)