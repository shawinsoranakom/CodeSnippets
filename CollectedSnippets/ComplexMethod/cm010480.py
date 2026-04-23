def _get_output_tensor_from_cache_entry(
        self,
        state: _CacheKeyState,
        entry: _DispatchCacheEntryOutputInfo,
        key: _DispatchCacheKey,
        func: OpOverload,
        args: Sequence[object],
    ) -> FakeTensor | None:
        if (
            entry.inplace_idx is None
            and entry.metadata is None
            and entry.view_idx is None
        ):
            if entry.constant_value is SingletonConstant:
                raise AssertionError(
                    "entry.constant_value must not be SingletonConstant"
                )
            return entry.constant_value
        if entry.inplace_idx is not None:
            # This is an in-place op; return the aliased arg.
            inplace_arg = args[entry.inplace_idx]
            if not isinstance(inplace_arg, FakeTensor):
                raise AssertionError("inplace_arg must be a FakeTensor")
            return inplace_arg

        # Synthesize a new FakeTensor with the cached metadata.
        metadata = entry.metadata
        if metadata is None:
            return None

        if is_sparse_any(metadata):
            raise AssertionError("Sparse tensors are not supported in cache")

        def check_value(value: _MetadataIntLike, state: _CacheKeyState) -> IntLikeType:
            if isinstance(value, _SymIntOutputStub):
                if state.shape_env is None:
                    raise AssertionError(
                        "state.shape_env must not be None for _SymIntOutputStub"
                    )
                return value.extract(key, state.shape_env)
            else:
                if isinstance(value, _PySymInputStub):
                    raise AssertionError("Unexpected _PySymInputStub value")
                return value

        shape = tuple(check_value(v, state) for v in metadata.shape)
        stride = tuple(check_value(v, state) for v in metadata.stride)
        storage_offset = check_value(metadata.storage_offset, state)
        if metadata.storage_bytes is not None:
            check_value(metadata.storage_bytes, state)

        maybe_suppress: Callable[[], typing.ContextManager[None]] = (
            contextlib.nullcontext
        )
        if self.shape_env is not None:
            maybe_suppress = self.shape_env.suppress_guards

        with in_kernel_invocation_manager(self), maybe_suppress():
            empty = torch.empty_strided(
                shape,
                stride,
                dtype=metadata.dtype,
                layout=metadata.layout,
                device="meta",
                requires_grad=metadata.requires_grad,
            )

        if metadata.is_conj:
            torch._C._set_conj(empty, True)
        if metadata.is_neg:
            torch._C._set_neg(empty, True)

        if isinstance(func, torch._ops.OpOverload) and func.is_view:
            # For view ops, the storage should be the same as the tensor input.
            view_arg = args[cast(int, entry.view_idx)]
            if not isinstance(view_arg, FakeTensor):
                raise AssertionError("view_arg must be a FakeTensor")
            storage = view_arg.untyped_storage()
            with in_kernel_invocation_manager(self), maybe_suppress():
                empty.set_(storage, storage_offset, shape, stride)

        return FakeTensor(self, empty, metadata.device)