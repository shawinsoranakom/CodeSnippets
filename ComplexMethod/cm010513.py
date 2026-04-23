def view_from_base(
            base: _TensorT,
            t: MetaTensorDesc[Any],
            shape_env: torch.fx.experimental.symbolic_shapes.ShapeEnv
            | None = shape_env,
        ) -> _TensorT:
            with enable_python_dispatcher():
                # fake-ify t's metadata according to the outer symbolic context
                (sizes, strides, storage_offset) = sym_sizes_strides_storage_offset(
                    t, source
                )
                if (
                    not t.is_traceable_wrapper_subclass
                    and not is_traceable_wrapper_subclass(base)
                ):
                    # Dense -> Dense view case uses as_strided() to construct view relationship.
                    # TODO: Change this logic to use view replay for consistency?
                    # It's likely there is no view func available.
                    with maybe_suppress():
                        return self._checked_cast_tensor_t(
                            base.as_strided(sizes, strides, storage_offset)
                        )

                from torch._dynamo.source import EphemeralSource
                from torch.fx.experimental.symbolic_shapes import (
                    StatelessSymbolicContext,
                    sym_eq,
                )

                def symint_visitor_fn(s: int) -> IntLikeType:
                    nonlocal symbolic_context
                    from torch.fx.experimental.symbolic_shapes import DimDynamic

                    all_static_sizes = (
                        symbolic_context is not None
                        and isinstance(symbolic_context, StatelessSymbolicContext)
                        and all(
                            x is DimDynamic.STATIC
                            for x in symbolic_context.dynamic_sizes
                        )
                    )
                    # Can't just rely on shape env being None - dynamo always initializes it
                    if all_static_sizes or shape_env is None:
                        return s

                    # NB: The symbol here is expected to be simplified out because we a priori
                    # allocate inner and outer symbols according to the appropriate symbolic
                    # contexts and prefer those over this symbol during symbol simplification
                    # (via usage of EphemeralSource below). This -shouldn't- happen, but if
                    # this symbol somehow leaks out beyond the view tensor's shape metadata, our
                    # assumption of it being simplified out will fail and it may be guarded on,
                    # which will hard error.
                    sym_source = EphemeralSource("symint_visitor_fn")

                    symbol = shape_env.create_symbol(s, sym_source, positive=None)
                    return shape_env.create_symintnode(
                        symbol, hint=s, source=sym_source
                    )

                real_to_fake_mapping = {}
                if t.is_traceable_wrapper_subclass:
                    if t.attrs is None:
                        raise AssertionError("t.attrs must not be None for subclass")
                    # NB: t.ctx could be None if the subclass in question has no
                    # meaningful context
                    if t.type is None:
                        raise AssertionError("t.type must not be None for subclass")

                    # Fake-ify t naively here; this is only done so we can get fake-ified inner
                    # tensors with the correct relationships to the outer sizes / strides for use
                    # in view replay. It's done beforehand here because it's not easy to do when
                    # visiting tensors one-by-one during view replay.
                    #
                    # Example:
                    #   Consider a Dense -> NJT view. NJT has (values, offsets) components and we
                    #   want a view of values with the offsets closed over. As the offsets component
                    #   is needed to describe the output view, it's important that it's fakeified
                    #   correctly.
                    fake_t: _TensorT = empty_create_subclass(
                        t, outer_size=sizes, outer_stride=strides
                    )
                    attrs, _ = fake_t.__tensor_flatten__()  # type: ignore[attr-defined]
                    for attr in attrs:
                        if attr in t.attrs:
                            real_to_fake_mapping[t.attrs[attr].id] = getattr(
                                fake_t, attr
                            )

                def tensor_visitor_fn(
                    visited_t: torch.Tensor,
                    # These arguments are never passed, we just use them to close
                    # over these relevant values
                    shape_env: torch.fx.experimental.symbolic_shapes.ShapeEnv
                    | None = shape_env,
                    callback: _MetaTensorCallbackOptDevice[_TensorT] = callback,
                ) -> torch.Tensor:
                    # It's possible to close over an undefined tensor (e.g. NJT's lengths).
                    if visited_t is None:
                        # pyrefly: ignore [bad-return]
                        return None

                    # NB: visited_t being a Tensor here is very naughty!  Should
                    # have already been described

                    # Fake inner tensors of view subclasses will come from the mapping built above.
                    visited_id = self.describer.get_tensor_id(visited_t)
                    fake_visited_t = real_to_fake_mapping.get(visited_id)
                    if fake_visited_t is not None:
                        return fake_visited_t

                    visited_desc = self.describer.describe_tensor(visited_t)

                    # For other closed-over tensor state, fake-ify it as all dynamic with an
                    # ephemeral source. This avoids invalid specialization during view replay.
                    # If we find that in practice the usage of ephemeral sources isn't enough
                    # to guarantee that we don't have guards on these symbols, we may need to
                    # explicitly suppress guards (as is done for _base in the dense -> dense
                    # view case).
                    temp_source = EphemeralSource("tensor_visitor_fn")
                    return self.meta_tensor(
                        visited_desc,
                        shape_env,
                        callback,
                        temp_source,
                        all_dynamic_symbolic_context(
                            visited_desc, temp_source, shape_env, callback
                        ),
                    )

                # Replay the view, swapping out any non-symbolic SymInts or real tensors
                # for symbolic SymInts or fake tensors.
                if t.view_func is None:
                    raise AssertionError("t.view_func must not be None for view replay")
                # NB: we do NOT suppress guards here, we need to remove ephemeral
                # sources
                fake_t = t.view_func.apply(
                    t,
                    base,
                    # pyrefly: ignore[bad-argument-type]
                    symint_visitor_fn,
                    tensor_visitor_fn,
                )

                # Ensure the output has symbolic shapes according to the outer symbolic context.
                # These checks should simplify out any symbols created for closed-over view func
                # SymInts.
                torch._check(sym_eq(fake_t.size(), sizes))
                torch._check(sym_eq(fake_t.stride(), strides))
                torch._check(sym_eq(fake_t.storage_offset(), storage_offset))
                return fake_t