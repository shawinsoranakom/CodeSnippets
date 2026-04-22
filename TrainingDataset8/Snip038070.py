def _install_tracer(self) -> None:
        """Install function that runs before each line of the script."""

        def trace_calls(frame, event, arg):
            self._maybe_handle_execution_control_request()
            return trace_calls

        # Python interpreters are not required to implement sys.settrace.
        if hasattr(sys, "settrace"):
            sys.settrace(trace_calls)