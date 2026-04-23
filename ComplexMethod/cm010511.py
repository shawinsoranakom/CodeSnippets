def sym_sizes_strides_storage_offset(
            t: MetaTensorDesc[Any],
            src: torch._guards.Source,
            symbolic_context: torch.fx.experimental.symbolic_shapes.SymbolicContext
            | None = symbolic_context,
        ) -> tuple[tuple[IntLikeType, ...], tuple[IntLikeType, ...], IntLikeType]:
            # local import to prevent circular import
            from torch.fx.experimental.symbolic_shapes import is_symbolic

            if t.stride is None:
                raise AssertionError("t.stride must not be None")

            if shape_env is not None:
                fake_mode = t.fake_mode
                has_symbolic = (
                    any(is_symbolic(sz) for sz in t.size)
                    or any(is_symbolic(sd) for sd in t.stride)
                    or is_symbolic(t.storage_offset)
                )
                if fake_mode is not None and fake_mode.shape_env is shape_env:
                    # Don't reallocate the sizes; the shape envs are the same,
                    # so reuse the old sizes/strides/etc
                    return (t.size, t.stride, t.storage_offset)
                elif (
                    fake_mode is not None
                    and not has_symbolic
                    and symbolic_context is None
                ):
                    return (t.size, t.stride, t.storage_offset)
                else:
                    # TODO: deduplicate this
                    t_size = tuple(
                        shape_env._maybe_specialize_sym_int_with_hint(sz)
                        for sz in t.size
                    )
                    t_stride = tuple(
                        shape_env._maybe_specialize_sym_int_with_hint(sd)
                        for sd in t.stride
                    )
                    t_storage_offset = shape_env._maybe_specialize_sym_int_with_hint(
                        t.storage_offset
                    )
                    return shape_env._create_symbolic_sizes_strides_storage_offset(
                        t_size,
                        t_stride,
                        t_storage_offset,
                        [d in t.dynamo_dynamic_indices for d in range(t.ndim)],
                        src,
                        symbolic_context=symbolic_context,
                        hint_overrides=t.dynamo_hint_overrides,
                    )
            else:
                return (t.size, t.stride, t.storage_offset)