def trace_func(frame, event, arg):
                frame.f_locals["self"].__class__
                if old_trace_func is not None:
                    old_trace_func(frame, event, arg)