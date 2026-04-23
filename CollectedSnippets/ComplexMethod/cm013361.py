def __torch_function__(self, func, types, args=(), kwargs=None):
        kwargs = kwargs if kwargs else {}

        # Only intercept calls to operators
        if not isinstance(func, (torch._ops.OpOverloadPacket, torch._ops.OpOverload)):
            return func(*args, **kwargs)
        if (
            torch.jit.is_tracing()
            or torch.jit.is_scripting()
            or torch._dynamo.is_compiling()
        ):
            return func(*args, **kwargs)
        # Pre-existing code may not use the .default overload. If we see an
        # OpOverloadPacket and we cannot resolve the overload, then we just throw
        # and ask the user to clarify. Otherwise, we attempt to resolve the overload.
        if isinstance(func, torch._ops.OpOverloadPacket):
            func = resolve_unique_overload_or_throw(func)
        qualname = func.name()
        ns = qualname.split("::")[0]
        if ns not in self.namespaces:
            return func(*args, **kwargs)

        args_c, kwargs_c = deepcopy_tensors((args, kwargs))
        result = func(*args, **kwargs)

        option = self.failures_dict.get_status(qualname, self.test_name)
        if option == "xsuccess" or option == "xfail":
            # Suppress all errors during execution. Raise them during __exit__.
            try:
                if qualname not in self.seen_ops_to_errors:
                    self.seen_ops_to_errors[qualname] = []
                self.run_test_util(func, args_c, kwargs_c)
            except Exception as ex:
                if should_print_better_repro():
                    self.seen_ops_to_errors[qualname].append((ex, func, args, kwargs))
                else:
                    self.seen_ops_to_errors[qualname].append((ex, func, None, None))
        elif option == "skip":
            pass
        return result