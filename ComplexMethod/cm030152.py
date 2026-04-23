async def set_trace_async(self, frame=None, *, commands=None):
        if self.async_awaitable is not None:
            # We are already in a set_trace_async call, do not mess with it
            return

        if frame is None:
            frame = sys._getframe().f_back

        # We need set_trace to set up the basics, however, this will call
        # set_stepinstr() will we need to compensate for, because we don't
        # want to trigger on calls
        self.set_trace(frame, commands=commands)
        # Changing the stopframe will disable trace dispatch on calls
        self.stopframe = frame
        # We need to stop tracing because we don't have the privilege to avoid
        # triggering tracing functions as normal, as we are not already in
        # tracing functions
        self.stop_trace()

        self.async_shim_frame = sys._getframe()
        self.async_awaitable = None

        while True:
            self.async_awaitable = None
            # Simulate a trace event
            # This should bring up pdb and make pdb believe it's debugging the
            # caller frame
            self.trace_dispatch(frame, "opcode", None)
            if self.async_awaitable is not None:
                try:
                    if self.breaks:
                        with self.set_enterframe(frame):
                            # set_continue requires enterframe to work
                            self.set_continue()
                        self.start_trace()
                    await self.async_awaitable
                except Exception:
                    self._error_exc()
            else:
                break

        self.async_shim_frame = None

        # start the trace (the actual command is already set by set_* calls)
        if self.returnframe is None and self.stoplineno == -1 and not self.breaks:
            # This means we did a continue without any breakpoints, we should not
            # start the trace
            return

        self.start_trace()