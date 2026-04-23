def dispatch_return(self, frame, arg):
        """Invoke user function and return trace function for return event.

        If the debugger stops on this function return, invoke
        self.user_return(). Raise BdbQuit if self.quitting is set.
        Return self.trace_dispatch to continue tracing in this scope.
        """
        if self.stop_here(frame) or frame == self.returnframe:
            # Ignore return events in generator except when stepping.
            if self.stopframe and frame.f_code.co_flags & GENERATOR_AND_COROUTINE_FLAGS:
                # It's possible to trigger a StopIteration exception in
                # the caller so we must set the trace function in the caller
                self._set_caller_tracefunc(frame)
                return self.trace_dispatch
            try:
                self.frame_returning = frame
                self.user_return(frame, arg)
                self.restart_events()
            finally:
                self.frame_returning = None
            if self.quitting: raise BdbQuit
            # The user issued a 'next' or 'until' command.
            if self.stopframe is frame and self.stoplineno != -1:
                self._set_stopinfo(None, None)
            # The previous frame might not have f_trace set, unless we are
            # issuing a command that does not expect to stop, we should set
            # f_trace
            if self.stoplineno != -1:
                self._set_caller_tracefunc(frame)
        return self.trace_dispatch