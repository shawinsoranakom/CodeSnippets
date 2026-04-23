def collect(self, stack_frames, timestamps_us=None):
        """Collect samples from stack frames.

        Args:
            stack_frames: List of interpreter/thread frame info
            timestamps_us: List of timestamps in microseconds (None for live sampling)
        """
        # Handle live sampling (no timestamps provided)
        if timestamps_us is None:
            current_time = (time.monotonic() * 1000) - self.start_time
            times = [current_time]
        else:
            if not timestamps_us:
                return
            # Initialize base timestamp if needed
            if self._replay_base_timestamp_us is None:
                self._replay_base_timestamp_us = timestamps_us[0]
            # Convert all timestamps to times (ms relative to first sample)
            base = self._replay_base_timestamp_us
            times = [(ts - base) / 1000 for ts in timestamps_us]

        first_time = times[0]

        # Update interval calculation
        if self.sample_count > 0 and self.last_sample_time > 0:
            self.interval = (times[-1] - self.last_sample_time) / self.sample_count
        self.last_sample_time = times[-1]

        # Process threads
        for interpreter_info in stack_frames:
            for thread_info in interpreter_info.threads:
                frames = filter_internal_frames(thread_info.frame_info)
                tid = thread_info.thread_id
                status_flags = thread_info.status
                is_main_thread = bool(status_flags & THREAD_STATUS_MAIN_THREAD)

                # Initialize thread if needed
                if tid not in self.threads:
                    self.threads[tid] = self._create_thread(tid, is_main_thread)

                thread_data = self.threads[tid]

                # Decode status flags
                has_gil = bool(status_flags & THREAD_STATUS_HAS_GIL)
                on_cpu = bool(status_flags & THREAD_STATUS_ON_CPU)
                gil_requested = bool(status_flags & THREAD_STATUS_GIL_REQUESTED)

                # Track state transitions using first timestamp
                self._track_state_transition(
                    tid, has_gil, self.has_gil_start, self.no_gil_start,
                    "Has GIL", "No GIL", CATEGORY_GIL, first_time
                )
                self._track_state_transition(
                    tid, on_cpu, self.on_cpu_start, self.off_cpu_start,
                    "On CPU", "Off CPU", CATEGORY_CPU, first_time
                )

                # Track code type
                if has_gil:
                    self._track_state_transition(
                        tid, True, self.python_code_start, self.native_code_start,
                        "Python Code", "Native Code", CATEGORY_CODE_TYPE, first_time
                    )
                elif on_cpu:
                    self._track_state_transition(
                        tid, True, self.native_code_start, self.python_code_start,
                        "Native Code", "Python Code", CATEGORY_CODE_TYPE, first_time
                    )
                else:
                    if tid in self.initialized_threads:
                        if tid in self.python_code_start:
                            self._add_marker(tid, "Python Code", self.python_code_start.pop(tid),
                                           first_time, CATEGORY_CODE_TYPE)
                        if tid in self.native_code_start:
                            self._add_marker(tid, "Native Code", self.native_code_start.pop(tid),
                                           first_time, CATEGORY_CODE_TYPE)

                # Track GIL wait
                if gil_requested:
                    self.gil_wait_start.setdefault(tid, first_time)
                elif tid in self.gil_wait_start:
                    self._add_marker(tid, "Waiting for GIL", self.gil_wait_start.pop(tid),
                                   first_time, CATEGORY_GIL)

                # Track exception state
                has_exception = bool(status_flags & THREAD_STATUS_HAS_EXCEPTION)
                self._track_state_transition(
                    tid, has_exception, self.exception_start, self.no_exception_start,
                    "Has Exception", "No Exception", CATEGORY_EXCEPTION, first_time
                )

                # Track GC events
                has_gc_frame = any(frame[2] == "<GC>" for frame in frames)
                if has_gc_frame:
                    if tid not in self.gc_start_per_thread:
                        self.gc_start_per_thread[tid] = first_time
                elif tid in self.gc_start_per_thread:
                    self._add_marker(tid, "GC Collecting", self.gc_start_per_thread.pop(tid),
                                   first_time, CATEGORY_GC)

                # Mark thread as initialized
                self.initialized_threads.add(tid)

                # Skip idle threads if requested
                is_idle = not has_gil and not on_cpu
                if self.skip_idle and is_idle:
                    continue

                if not frames:
                    continue

                # Process stack once to get stack_index
                stack_index = self._process_stack(thread_data, frames)

                # Add samples with timestamps
                samples = thread_data["samples"]
                samples_stack = samples["stack"]
                samples_time = samples["time"]
                samples_delay = samples["eventDelay"]

                for t in times:
                    samples_stack.append(stack_index)
                    samples_time.append(t)
                    samples_delay.append(None)

                # Handle opcodes
                if self.opcodes_enabled and frames:
                    leaf_frame = frames[0]
                    filename, location, funcname, opcode = leaf_frame
                    if isinstance(location, tuple):
                        lineno, _, col_offset, _ = location
                    else:
                        lineno = location
                        col_offset = -1

                    current_state = (opcode, lineno, col_offset, funcname, filename)

                    if tid not in self.opcode_state:
                        self.opcode_state[tid] = (*current_state, first_time)
                    elif self.opcode_state[tid][:5] != current_state:
                        prev_opcode, prev_lineno, prev_col, prev_funcname, prev_filename, prev_start = self.opcode_state[tid]
                        self._add_opcode_interval_marker(
                            tid, prev_opcode, prev_lineno, prev_col, prev_funcname, prev_start, first_time
                        )
                        self.opcode_state[tid] = (*current_state, first_time)

        self.sample_count += len(times)