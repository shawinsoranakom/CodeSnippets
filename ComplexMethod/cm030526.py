def process_frames(self, frames, thread_id=None):
        """Process a single thread's frame stack.

        Args:
            frames: List of frame information
            thread_id: Thread ID for per-thread tracking (optional)
        """
        if not frames:
            return

        # Get per-thread data if tracking per-thread
        thread_data = self._get_or_create_thread_data(thread_id) if thread_id is not None else None
        self._seen_locations.clear()

        # Process each frame in the stack to track cumulative calls
        # frame.location is (lineno, end_lineno, col_offset, end_col_offset), int, or None
        for frame in frames:
            lineno = extract_lineno(frame.location)
            location = (frame.filename, lineno, frame.funcname)
            if location not in self._seen_locations:
                self._seen_locations.add(location)
                self.result[location]["cumulative_calls"] += 1
                if thread_data:
                    thread_data.result[location]["cumulative_calls"] += 1

        # The top frame gets counted as an inline call (directly executing)
        top_frame = frames[0]
        top_lineno = extract_lineno(top_frame.location)
        top_location = (top_frame.filename, top_lineno, top_frame.funcname)
        self.result[top_location]["direct_calls"] += 1
        if thread_data:
            thread_data.result[top_location]["direct_calls"] += 1

        # Track opcode for top frame (the actively executing instruction)
        opcode = getattr(top_frame, 'opcode', None)
        if opcode is not None:
            self.opcode_stats[top_location][opcode] += 1
            if thread_data:
                thread_data.opcode_stats[top_location][opcode] += 1