def _get_output_info_for_cache_entry(
        self,
        state: _CacheKeyState,
        key: _DispatchCacheKey,
        func: OpOverload,
        args: Sequence[object],
        kwargs: Mapping[str, object],
        output: FakeTensor,
    ) -> _DispatchCacheEntryOutputInfo:
        if isinstance(output, (int, torch.SymInt, type(None))):
            return _DispatchCacheEntryOutputInfo(
                inplace_idx=None, metadata=None, view_idx=None, constant_value=output
            )

        # If this is an in-place op, the entry records which input arg is aliased.
        for idx in range(len(args)):
            if id(args[idx]) == id(output):
                return _DispatchCacheEntryOutputInfo(
                    inplace_idx=idx, metadata=None, view_idx=None
                )

        # Otherwise, create an entry that records the output tensor's metadata.
        view_idx = None
        if isinstance(func, torch._ops.OpOverload) and func.is_view:
            idxs = [i for i, t in enumerate(args) if isinstance(t, Tensor)]
            if len(idxs) != 1:
                raise AssertionError(
                    f"Expected exactly one tensor arg for view op, got {len(idxs)}"
                )
            view_idx = idxs[0]

        metadata = extract_tensor_metadata(output)
        metadata.shape = tuple(state.convert_output(v) for v in metadata.shape)
        metadata.stride = tuple(state.convert_output(v) for v in metadata.stride)
        metadata.storage_offset = state.convert_output(metadata.storage_offset)
        metadata.storage_bytes = (
            None
            if metadata.storage_bytes is None
            else state.convert_output(metadata.storage_bytes)
        )

        entry = _DispatchCacheEntryOutputInfo(
            inplace_idx=None,
            metadata=metadata,
            view_idx=view_idx,
        )

        # N.B.: Some checks for bypassing the cache would be performed on the
        # output tensor synthesized from the cached metadata. As an optimization,
        # we can synthesize a tensor here and do the checks on that instance.
        # This approach keeps the (more frequent) cache-hit path as lightweight
        # as possible.
        entry_for_synth_output = _DispatchCacheValidEntry(
            output_infos=(entry,), is_output_tuple=False
        )
        from torch.fx.experimental.symbolic_shapes import GuardOnDataDependentSymNode

        try:
            synth_output = self._output_from_cache_entry(
                state, entry_for_synth_output, key, func, args
            )
        except GuardOnDataDependentSymNode:
            # This should probably never really happen. If it does it means that
            # although the original call didn't get a data-dependent error when
            # we tried to reconstruct the output we did - that's almost
            # certainly a bug.
            raise _BypassDispatchCache("data dependent symnode") from None

        # Make sure the dispatch_key_set from the synthesized output tensor will
        # be the same.
        synth_key_set = torch._C._dispatch_key_set(synth_output)
        key_set = torch._C._dispatch_key_set(output)
        if synth_key_set != key_set:
            raise _BypassDispatchCache("dispatch_key_set mismatch")

        return entry