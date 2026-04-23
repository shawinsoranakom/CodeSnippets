def dispatch(self, /, dispatch_key, *args, **kwargs):
        from torch.utils._python_dispatch import _get_current_dispatch_mode

        if dispatch_key in self._dispatch_cache:
            kernel = self._dispatch_cache[dispatch_key]
            if isinstance(kernel, DispatchKey):
                raise AssertionError(f"unexpected DispatchKey in cache: {kernel}")
            return kernel(*args, **kwargs)

        if dispatch_key == DispatchKey.FuncTorchDynamicLayerFrontMode:
            return dispatch_functorch(self, args, kwargs)

        if dispatch_key == DispatchKey.Python:
            # Keep the following 1:1 with handle_torch_function_no_python_arg_parser
            # in torch/csrc/utils/python_arg_parser.cpp

            overloaded_args_list = []

            def has_python_key(tensor):
                return torch._C._dispatch_keys(tensor).has("Python")

            def check_overloaded(arg):
                if isinstance(arg, torch.Tensor) and has_python_key(arg):
                    overloaded_args_list.append(arg)

            for arg in (*args, *kwargs.values()):
                check_overloaded(arg)
                if isinstance(arg, (list, tuple)):
                    for a in arg:
                        check_overloaded(a)

            overloaded_args = tuple(overloaded_args_list)

            # Step 1: dispatch on any user TorchDispatchModes
            from torch.utils._python_dispatch import _pop_mode_temporarily

            curr_mode = _get_current_dispatch_mode()
            if curr_mode is not None:
                if type(curr_mode) in self.python_key_table:
                    handler = self.python_key_table[type(curr_mode)]
                    with _pop_mode_temporarily() as mode:
                        # "natural" calling convention: (mode, *args, **kwargs)
                        # TODO(rzou): we should support torch_dispatch calling convention too.
                        result = handler(mode, *args, **kwargs)
                else:
                    if curr_mode.supports_higher_order_operators:
                        with _pop_mode_temporarily() as mode:
                            return curr_mode.__torch_dispatch__(self, [], args, kwargs)
                    else:
                        raise NotImplementedError(
                            f"There was no rule registered for HigherOrderOperator {self._name} and mode {curr_mode}."
                            f"Hint: set {curr_mode}'s supports_higher_order_operators to True."
                            f" This causes all higher order operators to pass through {curr_mode}'s __torch_dispatch__,"
                            f" so handle them accordingly by"
                            f" adding support for HigerOrderOperators (in this case, {self._name}) in"
                            f" {curr_mode}.__torch_dispatch__ or"
                            f" returning NotImplemented when not supported."
                        )
                if result is not NotImplemented:
                    return result

            # Step 2: dispatch on any subclasses
            for arg in overloaded_args:
                subclass_type = type(arg)
                if (
                    subclass_type.__torch_dispatch__
                    is torch._C._disabled_torch_dispatch_impl
                ):
                    continue

                # In some case, people are using FakeTensor without a FakeTensorMode.
                # For example, some sparse arch model has a mix of FakeTensor and real
                # tensor for weights during lowering, and ppl tends to run eager evaluation
                # on the model without setting up the FakeTensorMode.
                # In this case, we pull FakeTensorMode impl.
                if subclass_type is torch._subclasses.fake_tensor.FakeTensor:
                    subclass_type = torch._subclasses.fake_tensor.FakeTensorMode  # type: ignore[assignment]
                    handler = self.python_key_table[subclass_type]
                    result = handler(arg.fake_mode, *args, **kwargs)  # type: ignore[attr-defined]
                    return result

                if subclass_type in self.python_key_table:
                    handler = self.python_key_table[subclass_type]
                    # "natural" calling convention: (*args, **kwargs)
                    # TODO(rzou): we should support torch_dispatch calling convention too.
                    result = handler(*args, **kwargs)
                else:
                    raise NotImplementedError(
                        f"There was no rule registered for HOP {self._name} and subclass {subclass_type}. "
                        f"We recommend filing an issue."
                    )
                if result is not NotImplemented:
                    return result

            # All handlers returned NotImplemented
            raise TypeError(
                f"HigherOrderOperator '{self._name}' is not supported for the given input types. "
                f"This typically happens when using custom tensor types or dispatch modes that don't "
                f"have implementations for this operation.\n\n"
                f"Current mode: {curr_mode}\n"
                f"Input types: {[type(a).__name__ for a in overloaded_args]}\n\n"
                f"To fix this, can add support for '{self._name}' in {curr_mode}'s __torch_dispatch__\n"
            )

        functionality_key = torch._C._to_functionality_key(dispatch_key)  # type: ignore[attr-defined]
        if functionality_key == DispatchKey.PreDispatch:
            from torch.utils._python_dispatch import _pop_mode_temporarily

            # The check for Python in the exclude set is so we properly respect `with no_dispatch()`
            # calls inside of a mode.
            if (
                _len_torch_dispatch_stack_pre_dispatch() > 0
            ) and not torch._C._dispatch_tls_is_dispatch_key_excluded(
                DispatchKey.Python
            ):
                curr_mode = _get_current_dispatch_mode_pre_dispatch()
                if curr_mode is None:
                    raise AssertionError(
                        "Illegal invocation of dispatch on DispatchKey.PreDispatch without a mode."
                    )
                if type(curr_mode) not in self.python_key_table:
                    raise AssertionError(
                        f"Current active mode {curr_mode} not registered"
                    )
                handler = self.python_key_table[type(curr_mode)]
                with _pop_mode_temporarily(functionality_key) as mode:
                    return handler(mode, *args, **kwargs)

        final_key = resolve_key(self, dispatch_key)

        # This can current fail due to backend fallbacks.  You just have to
        # register them by hand for HigherOrderOperator.
        if final_key not in self.py_kernels:
            raise NotImplementedError(
                f"could not find kernel for HigherOrderOperator {self._name} "
                f"at dispatch key {final_key} (resolved from {dispatch_key})"
            )

        # [NOTE] We shouldn't cache PreDispatch kernel here because depending
        # on what modes are active, predispatch behaviour is different.
        # Also we do same thing for normal ops:
        # See Note [Not Caching Per-Dispatch-Key Mode Handlers]
        if dispatch_key != DispatchKey.PreDispatch:
            self._dispatch_cache[dispatch_key] = self.py_kernels[final_key]
        kernel = self.py_kernels[final_key]
        # It's illegal to register DispatchKey to py_kernels, since there's no
        # C++ kernel to call into
        if isinstance(kernel, DispatchKey):
            raise AssertionError(f"unexpected DispatchKey in py_kernels: {kernel}")
        return kernel(*args, **kwargs)