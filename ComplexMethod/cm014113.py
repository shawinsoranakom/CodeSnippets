def _automatic_dynamic(
    e: Any,
    tx: "InstructionTranslatorBase",
    source: Source,
    static_shapes: bool,
    outer_only: bool = False,
) -> SymbolicContext:
    # strided NT not supported
    if e.is_nested and not isinstance(
        e, torch.nested._internal.nested_tensor.NestedTensor
    ):
        unimplemented(
            gb_type="Encountered strided NestedTensor in automatic dynamic dim determination",
            context="",
            explanation="torch.compile does not support strided NestedTensor",
            hints=[],
        )

    name = source.name
    prior_policy = tx.output.tracing_context.tensor_to_context.get(e, None)
    shape_env_to_source_to_symbol_cache = (
        prior_policy.shape_env_to_source_to_symbol_cache if prior_policy else {}
    )

    # Get base context if the tensor is a view
    view_base_context: SymbolicContext | None = None
    if e._is_view():
        base_source = AttrSource(source, "_base")
        view_base_context = _automatic_dynamic(e._base, tx, base_source, static_shapes)

    if is_traceable_wrapper_subclass(e) and not outer_only:
        # Get symbolic context for outer tensor
        outer_context = _automatic_dynamic(
            e, tx, source, static_shapes, outer_only=True
        )
        assert isinstance(outer_context, StatefulSymbolicContext)

        # Get symbolic contexts for inner tensors
        inner_contexts = {}  # mapping from attr -> symbolic context
        attrs, _ = type(e).__tensor_flatten__(e)
        for attr in attrs:
            match getattr(e, attr):
                case torch.Tensor() as inner_value:
                    inner_source = AttrSource(source, attr)
                    inner_contexts[attr] = _automatic_dynamic(
                        inner_value, tx, inner_source, static_shapes
                    )
                case OpaqueBase():
                    pass
                case unexpected:
                    raise AssertionError(
                        f"expected Tensor or OpaqueBase, got {type(unexpected)}"
                    )

        return SubclassSymbolicContext(
            dynamic_sizes=outer_context.dynamic_sizes,
            dynamic_strides=outer_context.dynamic_strides,
            constraint_sizes=outer_context.constraint_sizes,
            constraint_strides=outer_context.constraint_strides,
            view_base_context=view_base_context,
            tensor_source=outer_context.tensor_source,
            shape_env_to_source_to_symbol_cache=outer_context.shape_env_to_source_to_symbol_cache,
            inner_contexts=inner_contexts,
        )

    if static_shapes and not is_dynamic_source(name):
        return StatefulSymbolicContext(
            dynamic_sizes=[DimDynamic.STATIC] * e.dim(),
            dynamic_strides=[DimDynamic.INFER_STRIDE] * e.dim(),
            constraint_sizes=[None] * e.dim(),
            constraint_strides=[None] * e.dim(),
            view_base_context=view_base_context,
            tensor_source=source,
            shape_env_to_source_to_symbol_cache=shape_env_to_source_to_symbol_cache,
        )

    # We preserve the dynamism of inputs. For example, when users call
    # make_fx(torch.cond, tracing_mode="symbolic")(*args), inputs have SymInt sizes.
    from torch.fx.experimental.symbolic_shapes import is_nested_int

    if any(isinstance(s, SymInt) and not is_nested_int(s) for s in e.size()):
        return StatefulSymbolicContext(
            dynamic_sizes=[
                DimDynamic.DYNAMIC if isinstance(s, SymInt) else DimDynamic.STATIC
                for s in e.size()
            ],
            dynamic_strides=[DimDynamic.INFER_STRIDE] * e.dim(),
            constraint_sizes=[None] * e.dim(),
            constraint_strides=[None] * e.dim(),
            view_base_context=view_base_context,
            tensor_source=source,
            shape_env_to_source_to_symbol_cache=shape_env_to_source_to_symbol_cache,
        )

    # Prep for automatic dynamic
    frame_state_entry = record_automatic_dynamic(tx, name, e)

    # TODO: index export_constraints ahead of time so we don't have to
    # do a linear scan every time here
    t_id = id(e)
    # pyrefly: ignore [implicit-any]
    dim2constraint = {}

    def update_dim2constraint(
        dim: int, constraint_range: "StrictMinMaxConstraint", name: str
    ) -> None:
        if dim in dim2constraint:
            from torch.fx.experimental.symbolic_shapes import StrictMinMaxConstraint

            old_constraint_range, old_name = dim2constraint[dim]
            new_constraint_range = StrictMinMaxConstraint(
                vr=constraint_range.vr & old_constraint_range.vr,
                warn_only=False,
            )
            # It is possible for (non-None) old_name and name to be different
            # but this will only happen the corresponding Dims can be derived equal.
            new_name = old_name or name
            dim2constraint[dim] = new_constraint_range, new_name
        else:
            dim2constraint[dim] = constraint_range, name

    from torch.export.dynamic_shapes import _RelaxedConstraint

    if tx.output.export_constraints is not None:
        # type: ignore[iterable]
        for constraint in tx.output.export_constraints:
            if isinstance(constraint, _RelaxedConstraint):
                continue
            if constraint.t_id == t_id:
                update_dim2constraint(
                    constraint.dim, constraint.constraint_range, constraint.name
                )

    dynamic_sizes = []
    dynamic_strides = []
    constraint_sizes = []
    constraint_strides = []
    specialize_on = []
    for i in range(e.dim()):
        # NB: mark dynamic has precedence over static
        marked_strict_unbacked = i in getattr(
            e, "_dynamo_strict_unbacked_indices", set()
        )
        marked_unbacked = i in getattr(e, "_dynamo_unbacked_indices", set())
        marked_dynamic = i in getattr(e, "_dynamo_dynamic_indices", set())
        marked_weak_dynamic = i in getattr(e, "_dynamo_weak_dynamic_indices", set())
        marked_static = i in getattr(e, "_dynamo_static_indices", set())

        specialize_on.append(getattr(e, "_specialize_on", {}).get(i, []))

        # Reflect the user directive in the frame_state
        # For dynamic, apply None always

        normalized_source_name = normalize_source_name(source.name)
        base_source = source
        if isinstance(base_source, ChainedSource):
            base_source = base_source.get_base()

        if marked_dynamic or (
            isinstance(base_source, LocalSource)
            and base_source.dynamism is not None
            # pyrefly: ignore[no-matching-overload]
            and dict(base_source.dynamism).get(normalized_source_name, {i: False})[i]
        ):
            # TODO: This can be batched
            # TODO: Doing this here is kind of sus, maybe better to set this
            # up when we initially created the FrameStateSizeEntry to bong
            # into the mutable state
            log.debug("automatic dynamic %s marked dynamic", name)
            mark_size = [auto_unset] * e.dim()
            # pyrefly: ignore [unsupported-operation]
            mark_size[i] = auto_dynamic
            # pyrefly: ignore [bad-argument-type]
            frame_state_entry |= FrameStateSizeEntry.make_size(size=mark_size)

        # NB: both static and dynamic have precedence over
        automatic_dynamic_size = (
            config.automatic_dynamic_shapes and frame_state_entry.is_size_dynamic(i)
        )
        # NB: previously, if size was dynamic, we wouldn't make its stride
        # dynamic.  But now, because of InferStride concept, we will properly
        # not make stride dynamic even if it's wobbling
        automatic_dynamic_stride = (
            config.automatic_dynamic_shapes and frame_state_entry.is_stride_dynamic(i)
        )

        if is_dynamic_source(name):
            log.debug("%s marked dynamic via source whitelist", name)
            automatic_dynamic_size = True

        if is_unbacked_source(name):
            log.debug("%s marked unbacked via source whitelist", name)
            automatic_dynamic_size = True

        automatic_dynamic = automatic_dynamic_size or automatic_dynamic_stride

        # We will process constraints first, as they will imply that we
        # have a dynamic dimension
        # Precedence: export constraints > eager constraints
        constraint = dim2constraint.get(i)
        if constraint is None:
            constraint_size = None
            constraint_stride = None
            if marked_dynamic and not config.allow_ignore_mark_dynamic:
                # constraint_stride is deliberaly kept None because no easy way to provide value ranges for mark dynamic
                constraint_stride = None
                if hasattr(e, "_dynamo_dynamic_range"):
                    dim_range = [
                        dr for dr in e._dynamo_dynamic_range if dr.dim == i
                    ].pop()
                    if dim_range.min is None and dim_range.max is None:
                        constraint_size = RelaxedUnspecConstraint(warn_only=False)
                    else:
                        from torch.fx.experimental.symbolic_shapes import (
                            StrictMinMaxConstraint,
                        )

                        constraint_size = StrictMinMaxConstraint(
                            vr=ValueRanges(lower=dim_range.min, upper=dim_range.max),
                            warn_only=False,
                        )
                else:
                    constraint_size = RelaxedUnspecConstraint(warn_only=False)
            elif marked_strict_unbacked:
                constraint_size = RelaxedUnspecConstraint(warn_only=False)
            elif not marked_static and automatic_dynamic:
                set_feature_use("dynamo.automatic_dynamic_shapes", True)
                if automatic_dynamic_size:
                    constraint_size = RelaxedUnspecConstraint(warn_only=True)
                if automatic_dynamic_stride:
                    constraint_stride = RelaxedUnspecConstraint(warn_only=True)
            else:
                if not marked_static and not config.automatic_dynamic_shapes:
                    set_feature_use("dynamo.automatic_dynamic_shapes", False)
                constraint_size = None
                constraint_stride = None
        else:
            constraint_size, name_ = constraint
            constraint_stride = None
            dim_name = f"{name}.size()[{i}]"
            tx.output.shape_env.source_name_to_debug_name[dim_name] = name_
        constraint_sizes.append(constraint_size)
        constraint_strides.append(constraint_stride)

        if marked_unbacked or is_unbacked_source(name):
            dynamic_size = DimDynamic.UNBACKED
        elif (
            constraint_size is not None
            or marked_dynamic
            or marked_weak_dynamic
            or is_nested_int(e.size()[i])
        ):
            # NB: We could assert static_shapes is False here, but it
            # seems better to allow the user to override symbolic_context in this
            # case
            if automatic_dynamic:
                dynamic_size = get_automatic_dynamic_shapes_mark_as()
            else:
                dynamic_size = DimDynamic.DYNAMIC
        elif static_shapes or config.assume_static_by_default or marked_static:
            dynamic_size = DimDynamic.STATIC
        else:
            # TODO: When does this show up?
            dynamic_size = DimDynamic.DUCK

        if constraint_stride is not None:
            dynamic_stride = DimDynamic.DYNAMIC
        else:
            dynamic_stride = DimDynamic.INFER_STRIDE

        dynamic_sizes.append(dynamic_size)
        dynamic_strides.append(dynamic_stride)

    return StatefulSymbolicContext(
        dynamic_sizes=dynamic_sizes,
        dynamic_strides=dynamic_strides,
        constraint_sizes=constraint_sizes,
        # pyrefly: ignore [bad-argument-type]
        constraint_strides=constraint_strides,
        specialize_on=specialize_on,
        view_base_context=view_base_context,
        tensor_source=source,
        shape_env_to_source_to_symbol_cache=shape_env_to_source_to_symbol_cache,
        shape_ids=getattr(e, "_dynamo_shape_ids", None),
        unbacked_bounds=getattr(e, "_dynamo_unbacked_bounds", None),
        excluded_sizes=frame_state_entry.excluded_sizes,
    )