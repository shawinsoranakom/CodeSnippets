def _validate_output_for_cache_entry(
        self,
        state: _CacheKeyState,
        key: _DispatchCacheKey,
        func: OpOverload,
        args: Sequence[object],
        kwargs: Mapping[str, object],
        output: FakeTensor | None,
    ) -> None:
        # Is this even possible? According to the signature this can be None but
        # not `int`. So either the signature is a lie or (part of) this line is
        # unnecessary...
        if isinstance(output, (int, type(None))):
            return

        # Check for symbolic content that should bypass caching - raises
        # _BypassDispatchCache if necessary.
        _validate_symbolic_output_for_caching(state, output)

        # Some ops return tuples of Tensors, but it's rare, so avoid
        # the complexity of caching other types.
        if not isinstance(output, FakeTensor):
            raise _BypassDispatchCache("non-FakeTensor output")

        # Avoid caching FakeTensors with constants attached since those
        # can be invalidated.
        if output.constant is not None:
            raise _BypassDispatchCache("constant attribute")

        # TODO: support caching sparse outputs?
        if output.is_sparse:
            raise _BypassDispatchCache("sparse output")

        if is_sparse_compressed(output):
            raise _BypassDispatchCache("sparse compressed output")

        # Can an in-place op really reference a kwarg? If so, then we need
        # to extend the implementation to handle it.
        for kval in kwargs.values():
            if id(kval) == id(output):
                raise _BypassDispatchCache("kwarg aliases output")