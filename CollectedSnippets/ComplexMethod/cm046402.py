def close(self) -> None:
        """Close progress bar."""
        if self.closed:
            return

        self.closed = True

        if not self.disable:
            # Final display
            if self.total and self.n >= self.total:
                self.n = self.total
                if self.n != self.last_print_n:  # Skip if 100% already shown
                    self._display(final=True)
            else:
                self._display(final=True)

            # Cleanup
            if self.leave:
                self.file.write("\n")
            else:
                self.file.write("\r\033[K")

            try:
                self.file.flush()
            except Exception:
                pass