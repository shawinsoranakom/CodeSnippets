def sample(self, collector, duration_sec=None, *, async_aware=False):
        sample_interval_sec = self.sample_interval_usec / 1_000_000
        num_samples = 0
        errors = 0
        interrupted = False
        running_time_sec = 0
        start_time = next_time = time.perf_counter()
        last_sample_time = start_time
        realtime_update_interval = 1.0  # Update every second
        last_realtime_update = start_time
        try:
            while duration_sec is None or running_time_sec < duration_sec:
                # Check if live collector wants to stop
                if hasattr(collector, 'running') and not collector.running:
                    break

                current_time = time.perf_counter()
                if next_time > current_time:
                    sleep_time = (next_time - current_time) * 0.9
                    if sleep_time > 0.0001:
                        time.sleep(sleep_time)
                elif next_time < current_time:
                    try:
                        with _pause_threads(self.unwinder, self.blocking):
                            if async_aware == "all":
                                stack_frames = self.unwinder.get_all_awaited_by()
                            elif async_aware == "running":
                                stack_frames = self.unwinder.get_async_stack_trace()
                            else:
                                stack_frames = self.unwinder.get_stack_trace()
                            collector.collect(stack_frames)
                    except ProcessLookupError as e:
                        running_time_sec = current_time - start_time
                        break
                    except (RuntimeError, UnicodeDecodeError, MemoryError, OSError):
                        collector.collect_failed_sample()
                        errors += 1
                    except Exception as e:
                        if not _is_process_running(self.pid):
                            break
                        raise e from None

                    # Track actual sampling intervals for real-time stats
                    if num_samples > 0:
                        actual_interval = current_time - last_sample_time
                        self.sample_intervals.append(
                            1.0 / actual_interval
                        )  # Convert to Hz
                        self.total_samples += 1

                        # Print real-time statistics if enabled
                        if (
                            self.realtime_stats
                            and (current_time - last_realtime_update)
                            >= realtime_update_interval
                        ):
                            self._print_realtime_stats()
                            last_realtime_update = current_time

                    last_sample_time = current_time
                    num_samples += 1
                    next_time += sample_interval_sec

                running_time_sec = time.perf_counter() - start_time
        except KeyboardInterrupt:
            interrupted = True
            running_time_sec = time.perf_counter() - start_time
            print("Interrupted by user.")

        # Clear real-time stats line if it was being displayed
        if self.realtime_stats and len(self.sample_intervals) > 0:
            print()  # Add newline after real-time stats

        sample_rate = num_samples / running_time_sec if running_time_sec > 0 else 0
        error_rate = (errors / num_samples) * 100 if num_samples > 0 else 0
        expected_samples = int(running_time_sec / sample_interval_sec)
        missed_samples = (expected_samples - num_samples) / expected_samples * 100 if expected_samples > 0 else 0

        # Don't print stats for live mode (curses is handling display)
        is_live_mode = LiveStatsCollector is not None and isinstance(collector, LiveStatsCollector)
        if not is_live_mode:
            s = "" if num_samples == 1 else "s"
            print(f"Captured {num_samples:n} sample{s} in {fmt(running_time_sec, 2)} seconds")
            print(f"Sample rate: {fmt(sample_rate, 2)} samples/sec")
            print(f"Error rate: {fmt(error_rate, 2)}")

            # Print unwinder stats if stats collection is enabled
            if self.collect_stats:
                self._print_unwinder_stats()

            if isinstance(collector, BinaryCollector):
                self._print_binary_stats(collector)

        # Pass stats to flamegraph collector if it's the right type
        if hasattr(collector, 'set_stats'):
            collector.set_stats(self.sample_interval_usec, running_time_sec, sample_rate, error_rate, missed_samples, mode=self.mode)

        if num_samples < expected_samples and not is_live_mode and not interrupted:
            print(
                f"Warning: missed {expected_samples - num_samples} samples "
                f"from the expected total of {expected_samples} "
                f"({fmt((expected_samples - num_samples) / expected_samples * 100, 2)}%)"
            )