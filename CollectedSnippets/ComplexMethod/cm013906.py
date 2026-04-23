def _interactive_prompt(self, state: DebuggerState) -> None:
        """Interactive prompt during debugging."""
        frame_stack = self._build_tracked_frame_stack(state)
        view_index = len(frame_stack) - 1
        view_state = frame_stack[view_index]

        self._print_context(view_state)

        while True:
            try:
                cmd = input("(bdb) ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nExiting debugger.")
                self._quitting = True
                raise KeyboardInterrupt from None

            if not cmd:
                cmd = state.last_command
            else:
                state.last_command = cmd

            parts = cmd.split(maxsplit=1)
            action = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else ""

            if action in ("s", "step"):
                state.step_mode = True
                self._stop_at_new_code = True
                # Parse optional count argument (e.g., "s 3" to step 3 times)
                if arg:
                    try:
                        count = int(arg)
                        state.step_count = (
                            count - 1
                        )  # -1 because we're about to execute one
                    except ValueError:
                        print(f"Invalid count: {arg}")
                        continue
                else:
                    state.step_count = 0
                return

            elif action in ("n", "next"):
                self._next_in_frame = view_state.frame
                if arg:
                    try:
                        count = int(arg)
                        self._next_count = count - 1
                    except ValueError:
                        print(f"Invalid count: {arg}")
                        continue
                else:
                    self._next_count = 0
                state.step_mode = False
                self._stop_at_new_code = False
                return

            elif action in ("c", "cont", "continue"):
                state.step_mode = False
                self._stop_at_new_code = False
                self._stop_after_return = False
                return

            elif action in ("r", "return"):
                self._return_from_frame = state.frame
                state.step_mode = False
                self._stop_at_new_code = False
                return

            elif action in ("u", "up"):
                count = 1
                if arg:
                    try:
                        count = int(arg)
                    except ValueError:
                        print(f"Invalid count: {arg}")
                        continue
                new_index = view_index - count
                if new_index < 0:
                    new_index = 0
                    print("Oldest tracked frame")
                view_index = new_index
                view_state = frame_stack[view_index]
                print(f"> {view_state.code.co_name}")
                self._print_context(view_state)

            elif action in ("d", "down"):
                count = 1
                if arg:
                    try:
                        count = int(arg)
                    except ValueError:
                        print(f"Invalid count: {arg}")
                        continue
                max_index = len(frame_stack) - 1
                new_index = view_index + count
                if new_index > max_index:
                    new_index = max_index
                    print("Newest tracked frame")
                view_index = new_index
                view_state = frame_stack[view_index]
                print(f"> {view_state.code.co_name}")
                self._print_context(view_state)

            elif action in ("bt", "w", "where"):
                for i, fs in enumerate(frame_stack):
                    marker = ">" if i == view_index else " "
                    idx = fs.offset_to_index.get(fs.current_offset, -1)
                    inst = fs.offset_to_inst.get(fs.current_offset)
                    inst_str = inst.opname if inst else "<unknown>"
                    print(
                        f"  {marker} [{i}] {fs.code.co_name} instruction {idx} ({inst_str})"
                    )

            elif action in ("v", "verbose"):
                self._verbose = not self._verbose
                status = "enabled" if self._verbose else "disabled"
                print(f"Verbose mode {status}.")

            elif action in ("l", "list"):
                # Like pdb:
                # - 'l' continues from last position (or centers on current if first time)
                # - 'l .' centers on current instruction
                # - 'l N' lists 11 instructions starting at N
                # - 'l first, last' lists range (if last < first, last is a count)
                num_lines = 11  # pdb default
                start: int | None = None
                end: int | None = None

                if arg == ".":
                    # Reset to current instruction
                    view_state.list_index = None
                elif arg:
                    # Check for range syntax: "first, last" or "first,last"
                    if "," in arg:
                        parts = arg.split(",", 1)
                        try:
                            first = int(parts[0].strip())
                            second = int(parts[1].strip())
                            if second < first:
                                # second is a count
                                start = first
                                end = first + second
                            else:
                                start = first
                                end = second + 1  # inclusive
                        except ValueError:
                            print(f"Invalid range: {arg}")
                            continue
                    else:
                        # Single number: start at that instruction
                        try:
                            start = int(arg)
                            end = start + num_lines
                        except ValueError:
                            print(f"Invalid argument: {arg}")
                            continue

                if start is None:
                    if view_state.list_index is None:
                        # Center on current instruction
                        current_idx = view_state.offset_to_index.get(
                            view_state.current_offset, 0
                        )
                        start = max(0, current_idx - num_lines // 2)
                    else:
                        start = view_state.list_index
                    end = start + num_lines

                assert end is not None
                end = min(len(view_state.instructions), end)
                if start >= len(view_state.instructions):
                    print("(End of bytecode)")
                else:
                    print(self._format_header(view_state))
                    for i in range(start, end):
                        inst = view_state.instructions[i]
                        if inst.offset is not None:
                            print(self._format_instruction(view_state, inst.offset))
                    print()
                    view_state.list_index = end

            elif action == "ll":
                self._disassemble(view_state)

            elif action == "locals":
                self._print_locals(view_state)

            elif action == "globals":
                self._print_globals(view_state, arg if arg else None)

            elif action == "stack":
                is_current = view_state is frame_stack[-1]
                self._print_stack(view_state, is_current_frame=is_current)

            elif action == "b":
                if arg:
                    try:
                        index = int(arg)
                        num_instructions = len(view_state.instructions)
                        if index < 0 or index >= num_instructions:
                            print(
                                f"Invalid instruction number: {index} "
                                f"(must be 0-{num_instructions - 1})"
                            )
                        else:
                            view_state.breakpoints.add(index)
                            print(f"Breakpoint set at instruction {index}")
                    except ValueError:
                        print(f"Invalid instruction number: {arg}")
                else:
                    print("\nBreakpoints:")
                    if not view_state.breakpoints:
                        print("  (none)")
                    else:
                        for bp_index in sorted(view_state.breakpoints):
                            if bp_index < len(view_state.instructions):
                                inst = view_state.instructions[bp_index]
                                if inst.offset is not None:
                                    print(
                                        f"  {self._format_instruction(view_state, inst.offset, mark_current=False)}"
                                    )
                    print()

            elif action == "cl":
                if arg:
                    try:
                        index = int(arg)
                        num_instructions = len(view_state.instructions)
                        if index < 0 or index >= num_instructions:
                            print(
                                f"Invalid instruction number: {index} "
                                f"(must be 0-{num_instructions - 1})"
                            )
                        elif index in view_state.breakpoints:
                            view_state.breakpoints.discard(index)
                            print(f"Breakpoint cleared at instruction {index}")
                        else:
                            print(f"No breakpoint at instruction {index}")
                    except ValueError:
                        print(f"Invalid instruction number: {arg}")

            elif action == "p":
                if arg:
                    try:
                        is_current = view_state is frame_stack[-1]
                        frame_globals = view_state.frame.f_globals
                        eval_locals = self._build_eval_locals(
                            view_state, is_current_frame=is_current
                        )
                        result = eval(arg, frame_globals, eval_locals)
                        print(f"{arg} = {result!r}")
                    except Exception as e:
                        print(f"Error evaluating '{arg}': {e}")
                else:
                    print("Usage: p <expression>")

            elif action in ("h", "help", "?"):
                self._print_help()

            elif action in ("q", "quit", "exit"):
                print("Exiting debugger.")
                self._quitting = True
                raise KeyboardInterrupt

            else:
                # Try to execute as Python code (like pdb)
                is_current = view_state is frame_stack[-1]
                frame_globals = view_state.frame.f_globals
                eval_locals = self._build_eval_locals(
                    view_state, is_current_frame=is_current
                )

                try:
                    # First try as expression (eval)
                    result = eval(cmd, frame_globals, eval_locals)
                    if result is not None:
                        print(repr(result))
                except SyntaxError:
                    # If not a valid expression, try as statement (exec)
                    try:
                        keys_before = set(eval_locals.keys())
                        ids_before = {k: id(v) for k, v in eval_locals.items()}
                        exec(cmd, frame_globals, eval_locals)
                        # Capture any new or modified variables into user_locals
                        for key in eval_locals:
                            is_new = key not in keys_before
                            is_user_var = key in view_state.user_locals
                            is_modified = id(eval_locals[key]) != ids_before.get(key)
                            if (
                                is_new or is_user_var or is_modified
                            ) and key != "__stack__":
                                view_state.user_locals[key] = eval_locals[key]
                    except Exception as e:
                        print(f"*** {type(e).__name__}: {e}")
                except Exception as e:
                    print(f"*** {type(e).__name__}: {e}")