def refresh(self) -> None:
        """Update the display of the Live Render."""
        with self._lock:
            self._live_render.set_renderable(self.renderable)
            if self._nested:
                if self.console._live_stack:
                    self.console._live_stack[0].refresh()
                return

            if self.console.is_jupyter:  # pragma: no cover
                try:
                    from IPython.display import display
                    from ipywidgets import Output
                except ImportError:
                    import warnings

                    warnings.warn('install "ipywidgets" for Jupyter support')
                else:
                    if self.ipy_widget is None:
                        self.ipy_widget = Output()
                        display(self.ipy_widget)

                    with self.ipy_widget:
                        self.ipy_widget.clear_output(wait=True)
                        self.console.print(self._live_render.renderable)
            elif self.console.is_terminal and not self.console.is_dumb_terminal:
                with self.console:
                    self.console.print(Control())
            elif (
                not self._started and not self.transient
            ):  # if it is finished allow files or dumb-terminals to see final result
                with self.console:
                    self.console.print(Control())