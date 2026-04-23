def _empty_create_subclass(
        self,
        t: MetaTensorDesc[Any],
        outer_size: tuple[int, ...] | None,
        outer_stride: tuple[int, ...] | None,
        shape_env: ShapeEnv | None,
        symbolic_context: torch.fx.experimental.symbolic_shapes.SymbolicContext | None,
        callback: _MetaTensorCallbackOptDevice[_TensorT],
        source: torch._guards.Source,
    ) -> _TensorT:
        from torch._dynamo.source import AttrSource
        from torch.fx.experimental.symbolic_shapes import SubclassSymbolicContext

        # We are hitting plain meta_desc tensor so actually
        # create a tensor here.
        if t.attrs is None:
            return self.meta_tensor(
                t,
                shape_env,
                callback,
                source,
                symbolic_context,
            )

        inner_tensors: dict[str, torch.Tensor | OpaqueBase] = {}
        for attr, meta_tensor_desc in t.attrs.items():
            current_context = None
            if symbolic_context is not None:
                if not isinstance(symbolic_context, SubclassSymbolicContext):
                    raise AssertionError(
                        f"Expected SubclassSymbolicContext, got {type(symbolic_context)}"
                    )
                if attr not in symbolic_context.inner_contexts:
                    raise AssertionError(
                        f"tensor attr {attr!r} missing from inner_contexts"
                    )
                if (
                    current_context_ := symbolic_context.inner_contexts[attr]
                ) is not None:
                    current_context = _checked_cast(
                        torch.fx.experimental.symbolic_shapes.SymbolicContext,
                        current_context_,
                    )

            current_source = AttrSource(source, attr)
            inner_callback = functools.partial(callback, device=meta_tensor_desc.device)
            new_empty_tensor = self._empty_create_subclass(
                meta_tensor_desc,
                meta_tensor_desc.size,
                meta_tensor_desc.stride,
                shape_env,
                current_context,
                inner_callback,
                current_source,
            )
            inner_tensors[attr] = new_empty_tensor

        # Pass through opaque (non-tensor) attrs
        if t.opaque_attrs:
            inner_tensors.update(t.opaque_attrs)

        if t.type is None:
            raise AssertionError("t.type must not be None for subclass")
        return t.type.__tensor_unflatten__(  # type: ignore[attr-defined]
            inner_tensors, t.ctx, outer_size, outer_stride
        )