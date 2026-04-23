def collect(self, stack_frames, timestamp_us=None):
        """Collect and display profiling data."""
        if self.start_time is None:
            self.start_time = time.perf_counter()
            self._last_display_update = self.start_time

        has_gc_frame = False

        # Collect thread status stats (only available in sync mode)
        if not self.async_aware:
            status_counts, sample_has_gc, per_thread_stats = self._collect_thread_status_stats(stack_frames)
            for key, count in status_counts.items():
                self.thread_status_counts[key] += count
            if sample_has_gc:
                has_gc_frame = True

            for thread_id, stats in per_thread_stats.items():
                thread_data = self._get_or_create_thread_data(thread_id)
                thread_data.has_gil += stats.get("has_gil", 0)
                thread_data.on_cpu += stats.get("on_cpu", 0)
                thread_data.gil_requested += stats.get("gil_requested", 0)
                thread_data.unknown += stats.get("unknown", 0)
                thread_data.has_exception += stats.get("has_exception", 0)
                thread_data.total += stats.get("total", 0)
                if stats.get("gc_samples", 0):
                    thread_data.gc_frame_samples += stats["gc_samples"]

        # Process frames using pre-selected iterator
        frames_processed = False
        for frames, thread_id in self._get_frame_iterator(stack_frames):
            if not frames:
                continue

            self.process_frames(frames, thread_id=thread_id)
            frames_processed = True

            # Track thread IDs
            if thread_id is not None and thread_id not in self.thread_ids:
                self.thread_ids.append(thread_id)

            if thread_id is not None:
                thread_data = self._get_or_create_thread_data(thread_id)
                thread_data.sample_count += 1

        if has_gc_frame:
            self.gc_frame_samples += 1

        # Count as successful - the sample worked even if no frames matched the filter
        # (e.g., in --mode exception when no thread has an active exception)
        self.successful_samples += 1
        self.total_samples += 1

        # Handle input on every sample for instant responsiveness
        if self.display is not None:
            self._handle_input()

        # Update display at configured rate if display is initialized and not paused
        if self.display is not None and not self.paused:
            current_time = time.perf_counter()
            if (
                self._last_display_update is None
                or (current_time - self._last_display_update)
                >= self.display_update_interval_sec
            ):
                self._update_display()
                self._last_display_update = current_time