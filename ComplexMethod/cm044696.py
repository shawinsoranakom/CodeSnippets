def stop(self) -> None:
        """Stop live rendering display."""
        with self._lock:
            if not self._started:
                return
            self._started = False
            self.console.clear_live()
            if self._nested:
                if not self.transient:
                    self.console.print(self.renderable)
                return

            if self.auto_refresh and self._refresh_thread is not None:
                self._refresh_thread.stop()
                self._refresh_thread = None
            # allow it to fully render on the last even if overflow
            self.vertical_overflow = "visible"
            with self.console:
                try:
                    if not self._alt_screen and not self.console.is_jupyter:
                        self.refresh()
                finally:
                    self._disable_redirect_io()
                    self.console.pop_render_hook()
                    if (
                        not self._alt_screen
                        and self.console.is_terminal
                        and self._live_render.last_render_height
                    ):
                        self.console.line()
                    self.console.show_cursor(True)
                    if self._alt_screen:
                        self.console.set_alt_screen(False)
                    if self.transient and not self._alt_screen:
                        self.console.control(self._live_render.restore_cursor())
                    if self.ipy_widget is not None and self.transient:
                        self.ipy_widget.close()