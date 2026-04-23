def _handle_input(self):
        """Handle keyboard input (non-blocking)."""
        self.display.set_nodelay(True)
        ch = self.display.get_input()

        # Handle filter input mode FIRST - takes precedence over all commands
        if self.filter_input_mode:
            if ch == 27:  # ESC key
                self.filter_input_mode = False
                self.filter_input_buffer = ""
            elif ch == 10 or ch == 13:  # Enter key
                self.filter_pattern = (
                    self.filter_input_buffer
                    if self.filter_input_buffer
                    else None
                )
                self.filter_input_mode = False
                self.filter_input_buffer = ""
            elif ch == 127 or ch == 263:  # Backspace
                if self.filter_input_buffer:
                    self.filter_input_buffer = self.filter_input_buffer[:-1]
            elif ch >= 32 and ch < 127:  # Printable characters
                self.filter_input_buffer += chr(ch)

            # Update display if input was processed while finished
            self._handle_finished_input_update(ch != -1)
            return

        # Handle help toggle keys
        if ch == ord("h") or ch == ord("H") or ch == ord("?"):
            self.show_help = not self.show_help
            return

        # If showing help, any other key closes it
        if self.show_help and ch != -1:
            self.show_help = False
            return

        # Handle regular commands
        if ch == ord("q") or ch == ord("Q"):
            self.running = False

        elif ch == ord("s"):
            self._cycle_sort(reverse=False)

        elif ch == ord("S"):
            self._cycle_sort(reverse=True)

        elif ch == ord("p") or ch == ord("P"):
            self.paused = not self.paused

        elif ch == ord("r") or ch == ord("R"):
            # Don't allow reset when profiling is finished
            if not self.finished:
                self.reset_stats()

        elif ch == ord("+") or ch == ord("="):
            # Decrease update interval (faster refresh)
            self.display_update_interval_sec = max(
                0.05, self.display_update_interval_sec - 0.05
            )  # Min 20Hz

        elif ch == ord("-") or ch == ord("_"):
            # Increase update interval (slower refresh)
            self.display_update_interval_sec = min(
                1.0, self.display_update_interval_sec + 0.05
            )  # Max 1Hz

        elif ch == ord("c") or ch == ord("C"):
            if self.filter_pattern:
                self.filter_pattern = None

        elif ch == ord("/"):
            self.filter_input_mode = True
            self.filter_input_buffer = self.filter_pattern or ""

        elif ch == ord("t") or ch == ord("T"):
            # Toggle between ALL and PER_THREAD modes
            if self.view_mode == "ALL":
                if len(self.thread_ids) > 0:
                    self.view_mode = "PER_THREAD"
                    self.current_thread_index = 0
            else:
                self.view_mode = "ALL"

        elif ch == ord("x") or ch == ord("X"):
            # Toggle trend colors on/off
            if self._trend_tracker is not None:
                self._trend_tracker.toggle()

        elif ch == ord("j") or ch == ord("J"):
            # Move selection down in opcode mode (with scrolling)
            self._move_selection_down()

        elif ch == ord("k") or ch == ord("K"):
            # Move selection up in opcode mode (with scrolling)
            self._move_selection_up()

        elif ch == curses.KEY_UP:
            # Move selection up (same as 'k') when in opcode mode
            if self.show_opcodes:
                self._move_selection_up()
            else:
                # Navigate to previous thread (same as KEY_LEFT)
                self._navigate_to_previous_thread()

        elif ch == curses.KEY_DOWN:
            # Move selection down (same as 'j') when in opcode mode
            if self.show_opcodes:
                self._move_selection_down()
            else:
                # Navigate to next thread (same as KEY_RIGHT)
                self._navigate_to_next_thread()

        elif ch == curses.KEY_LEFT:
            # Navigate to previous thread
            self._navigate_to_previous_thread()

        elif ch == curses.KEY_RIGHT:
            # Navigate to next thread
            self._navigate_to_next_thread()

        # Update display if input was processed while finished
        self._handle_finished_input_update(ch != -1)