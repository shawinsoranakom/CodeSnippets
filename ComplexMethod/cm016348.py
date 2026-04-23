def dynamic_context(self, frame: Any) -> None:
        if frame.f_code.co_name == "should_drop":
            obj = frame.f_locals["fn"]
            # The many conditions in the if statement below are based on the accepted arguments to getsourcefile. Based
            # on its documentation (https://docs.python.org/3/library/inspect.html#inspect.getsourcefile), the argument
            # must be a module, class, method, function, traceback, frame, or code object AND it cannot be a built-in
            # module, class, or function.
            # Currently, we DO NOT include tracebacks or frames as they should not be JIT'd, and we have not checked for
            # built-in modules or functions as those do not seem to be JIT'd either.
            if (
                is_not_builtin_class(obj)
                or ismodule(obj)
                or ismethod(obj)
                or isfunction(obj)
                or iscode(obj)
            ):
                filename = getsourcefile(obj)
                # We don't want to report for filename = None
                if filename:
                    # TODO: Because torch.jit._IgnoreContextManager relies on Python's `exec` method
                    # which doesn't generate source codelines, getsourcelines(obj) fails. For now,
                    # we just ignore the exception until we figure out a better way to
                    # implement torch.jit._IgnoreContextManager.
                    try:
                        sourcelines, starting_lineno = getsourcelines(obj)
                    except OSError:
                        pass
                    else:
                        line_data = {
                            filename: range(
                                starting_lineno, starting_lineno + len(sourcelines)
                            )
                        }
                        cov_data.add_lines(line_data)
        super().dynamic_context(frame)