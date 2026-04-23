def _queue_log(self, text):
        """Queue console text with deduplication and timestamp processing."""
        if not self.active:
            return

        current_time = time.time()

        # Handle carriage returns and process lines
        if "\r" in text:
            text = text.split("\r")[-1]

        lines = text.split("\n")
        if lines and lines[-1] == "":
            lines.pop()

        for line in lines:
            line = line.rstrip()

            # Skip lines with only thin progress bars (partial progress)
            if "─" in line:  # Has thin lines but no thick lines
                continue

            # Only show 100% completion lines for progress bars
            if " ━━" in line:
                is_complete = "100%" in line

                # Skip ALL non-complete progress lines
                if not is_complete:
                    continue

                # Extract sequence key to deduplicate multiple 100% lines for same sequence
                parts = line.split()
                seq_key = ""
                if parts:
                    # Check for epoch pattern (X/Y at start)
                    if "/" in parts[0] and parts[0].replace("/", "").isdigit():
                        seq_key = parts[0]  # e.g., "1/3"
                    elif parts[0] == "Class" and len(parts) > 1:
                        seq_key = f"{parts[0]}_{parts[1]}"  # e.g., "Class_train:" or "Class_val:"
                    elif parts[0] in ("train:", "val:"):
                        seq_key = parts[0]  # Phase identifier

                # Skip if we already showed 100% for this sequence
                if seq_key and self.last_progress_line == f"{seq_key}:done":
                    continue

                # Mark this sequence as done
                if seq_key:
                    self.last_progress_line = f"{seq_key}:done"

                self.last_was_progress = True
            else:
                # Skip empty line after progress bar
                if not line and self.last_was_progress:
                    self.last_was_progress = False
                    continue
                self.last_was_progress = False

            # General deduplication
            if line == self.last_line and current_time - self.last_time < 0.1:
                continue

            self.last_line = line
            self.last_time = current_time

            # Add timestamp if needed
            if not line.startswith("[20"):
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                line = f"[{timestamp}] {line}"

            # Add to buffer and check if flush needed
            should_flush = False
            with self.buffer_lock:
                self.buffer.append(line)
                if len(self.buffer) >= self.batch_size:
                    should_flush = True

            # Flush outside lock to avoid deadlock
            if should_flush:
                self._flush_buffer()