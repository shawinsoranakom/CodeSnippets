def _get_dispatch(self, key: DispatchKey) -> DispatchKey | Callable[_P, _T]:
        # This is only called upon a cache miss
        if key in self._dispatch_cache:
            raise AssertionError(f"{self} {key} already in dispatch cache")

        if key == DispatchKey.Python:
            if not isinstance(self, TorchBindOpOverload) and not self.python_key_table:
                self._dispatch_cache[key] = key
                add_cached_op(self)
                return key

            def handler(*args: _P.args, **kwargs: _P.kwargs) -> _T:
                from torch.utils._python_dispatch import _get_current_dispatch_mode

                # TODO: We also need to handle tensor subclasses here
                # TODO(voz): We should walk all the nodes here / turn it into a list, topmode is ok for now.
                curr_mode = type(_get_current_dispatch_mode())
                if curr_mode is None:
                    raise AssertionError(
                        "Illegal invocation of dispatch on DispatchKey.Python without a mode."
                    )

                if curr_mode not in self.python_key_table:
                    if isinstance(self, TorchBindOpOverload):
                        with (
                            torch.utils._python_dispatch._pop_mode_temporarily() as mode
                        ):
                            return torch._library.utils.handle_dispatch_mode(
                                mode, self, *args, **kwargs
                            )
                    else:
                        return self._op_dk(key, *args, **kwargs)

                with torch.utils._python_dispatch._pop_mode_temporarily() as mode:
                    return self.python_key_table[curr_mode](mode, *args, **kwargs)  # type: ignore[index]

            self._dispatch_cache[key] = handler
            add_cached_op(self)
            return handler

        functionality_key = torch._C._to_functionality_key(key)  # type: ignore[attr-defined]
        if functionality_key == DispatchKey.PreDispatch:
            curr_stack_len = _len_torch_dispatch_stack_pre_dispatch()
            # The check for Python in the exclude set is so we properly respect `with no_dispatch()`
            # calls inside of a mode.
            if (
                curr_stack_len > 0
                and not torch._C._dispatch_tls_is_dispatch_key_excluded(
                    DispatchKey.Python
                )
            ):

                def handler(*args: _P.args, **kwargs: _P.kwargs) -> _T:
                    @contextlib.contextmanager
                    def _temporarily_pop_modes_from_pre_dispatch():
                        top_mode = _pop_mode_from_pre_dispatch()
                        try:
                            yield top_mode
                        finally:
                            _set_mode_pre_dispatch(top_mode)

                    with _temporarily_pop_modes_from_pre_dispatch() as curr_mode:
                        return torch._library.utils.handle_dispatch_mode(
                            curr_mode, self, *args, **kwargs
                        )

                # Note [Not Caching Per-Dispatch-Key Mode Handlers]
                # Note that we're not caching this handler.  There isn't really a point, since the slow bit
                # is the handler itself (in python).
                # Also, not caching means that we don't have to reset the cache when any existing
                # modes go out of scope (which in of itself takes time to loop through all operators).
                return handler

        final_key = resolve_key(self, key)

        # See Note [Not Caching Per-Dispatch-Key Mode Handlers]
        cache_result = key != DispatchKey.PreDispatch

        # TODO: We could potentially have lots of debugging wrappers against
        # dispatch keys; design some general registration mechanism instead of
        # having if statement for each of them
        if key == DispatchKey.Functionalize:
            import torch._dispatch.python as pydispatch

            if pydispatch.CROSSREF_FUNCTIONALIZE:
                handler = pydispatch.make_crossref_functionalize(self, final_key)  # type: ignore[assignment]
                if cache_result:
                    self._dispatch_cache[key] = handler
                    add_cached_op(self)
                return handler

        r = self.py_kernels.get(final_key, final_key)
        if cache_result:
            self._dispatch_cache[key] = r
            add_cached_op(self)
        return r