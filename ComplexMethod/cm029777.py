def dispatch_exception(self, frame, arg):
        """Invoke user function and return trace function for exception event.

        If the debugger stops on this exception, invoke
        self.user_exception(). Raise BdbQuit if self.quitting is set.
        Return self.trace_dispatch to continue tracing in this scope.
        """
        if self.stop_here(frame):
            # When stepping with next/until/return in a generator frame, skip
            # the internal StopIteration exception (with no traceback)
            # triggered by a subiterator run with the 'yield from' statement.
            if not (frame.f_code.co_flags & GENERATOR_AND_COROUTINE_FLAGS
                    and arg[0] is StopIteration and arg[2] is None):
                self.user_exception(frame, arg)
                self.restart_events()
                if self.quitting: raise BdbQuit
        # Stop at the StopIteration or GeneratorExit exception when the user
        # has set stopframe in a generator by issuing a return command, or a
        # next/until command at the last statement in the generator before the
        # exception.
        elif (self.stopframe and frame is not self.stopframe
                and self.stopframe.f_code.co_flags & GENERATOR_AND_COROUTINE_FLAGS
                and arg[0] in (StopIteration, GeneratorExit)):
            self.user_exception(frame, arg)
            self.restart_events()
            if self.quitting: raise BdbQuit

        return self.trace_dispatch