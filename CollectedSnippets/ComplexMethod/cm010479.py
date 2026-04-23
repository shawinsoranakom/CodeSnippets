def _make_cache_entry(
        self,
        state: _CacheKeyState,
        key: _DispatchCacheKey,
        func: OpOverload,
        args: Sequence[object],
        kwargs: Mapping[str, object],
        output: FakeTensor | None,
    ) -> _DispatchCacheValidEntry:
        """
        Make a cache entry object for the given 'output' Tensor. Raises
        _BypassDispatchCache if the output tensor has characteristics that
        prevent caching it.
        """
        from torch._higher_order_ops.utils import registered_hop_fake_fns
        from torch.fx.experimental.symbolic_shapes import has_free_unbacked_symbols

        self._validate_cache_key(func, args, kwargs)

        # For hops, lets look at the output tensor to find any unbacked symints.
        # If there are none, then we rely on the existing checks to validate
        # caching.
        # NB: Note that the HOPs that sta alive till FakeTensor are functional,
        # once they support mutations, we will have to revisit this logic.
        if (
            isinstance(func, torch._ops.HigherOrderOperator)
            and func in registered_hop_fake_fns
        ):
            if not isinstance(output, tuple) and output is not None:
                raise AssertionError(
                    f"Expected tuple output for HOP {func}, got {type(output)}"
                )
            if output is not None:
                non_cacheable = any(
                    isinstance(o, (torch.Tensor, torch.SymInt))
                    and has_free_unbacked_symbols(o)
                    for o in output  # pyrefly: ignore[not-iterable]
                )
                if non_cacheable:
                    raise _BypassDispatchCache(f"unbacked symbol in HOP {func} output")

        if isinstance(output, (int, torch.SymInt, type(None))):
            output_info = _DispatchCacheEntryOutputInfo(
                inplace_idx=None, metadata=None, view_idx=None, constant_value=output
            )
            return _DispatchCacheValidEntry(
                output_infos=(output_info,), is_output_tuple=False
            )

        if isinstance(output, tuple):
            for out_element in output:
                self._validate_output_for_cache_entry(
                    state,
                    key,
                    func,
                    args,
                    kwargs,
                    out_element,
                )
        else:
            self._validate_output_for_cache_entry(
                state,
                key,
                func,
                args,
                kwargs,
                output,
            )

        if isinstance(output, tuple):
            output_infos = [
                self._get_output_info_for_cache_entry(
                    state,
                    key,
                    func,
                    args,
                    kwargs,
                    out_elem,
                )
                for out_elem in output
            ]
            return _DispatchCacheValidEntry(
                # pyrefly: ignore [bad-argument-type]
                output_infos=tuple(output_infos),
                is_output_tuple=True,
            )

        else:
            output_info = self._get_output_info_for_cache_entry(
                state,
                key,
                func,
                args,
                kwargs,
                output,
            )
            return _DispatchCacheValidEntry(
                output_infos=(output_info,), is_output_tuple=False
            )