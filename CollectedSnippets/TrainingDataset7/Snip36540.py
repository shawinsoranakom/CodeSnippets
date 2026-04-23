def test_trace(self):
        # See ticket #19456
        old_trace_func = sys.gettrace()
        try:

            def trace_func(frame, event, arg):
                frame.f_locals["self"].__class__
                if old_trace_func is not None:
                    old_trace_func(frame, event, arg)

            sys.settrace(trace_func)
            self.lazy_wrap(None)
        finally:
            sys.settrace(old_trace_func)