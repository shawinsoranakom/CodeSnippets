def _create_symbolic_context_for_tensor(t, source, t_constraints, sources, mode):
    """Helper function to create symbolic context for a tensor."""
    from torch._dynamo.source import AttrSource
    from torch.fx.experimental.symbolic_shapes import (
        DimDynamic,
        RelaxedUnspecConstraint,
        SubclassSymbolicContext,
    )
    from torch.utils._python_dispatch import is_traceable_wrapper_subclass

    # Common dynamic dimension logic for both regular tensors and subclasses
    n_dims = len(t.shape)
    dynamic_sizes = []
    constraint_sizes = [None] * n_dims

    for i in range(n_dims):
        if i in getattr(t, "_dynamo_weak_dynamic_indices", {}):
            dynamic_sizes.append(DimDynamic.DYNAMIC)
        elif i in getattr(t, "_dynamo_dynamic_indices", {}):
            # bit annoying, but we need to replicate process in _dynamo/variables/builder.py
            # where a RelaxedUnspecConstraint is created for Dim.DYNAMIC, so constraint violations
            # are raised when specializing.
            dynamic_sizes.append(DimDynamic.DYNAMIC)
            constraint_sizes[i] = RelaxedUnspecConstraint(warn_only=False)  # type: ignore[call-overload]
        else:
            dynamic_sizes.append(DimDynamic.STATIC)

    # Handle nested subclasses
    if is_traceable_wrapper_subclass(t):
        # Get inner contexts recursively
        inner_contexts = {}
        attrs, _ = type(t).__tensor_flatten__(t)

        # Propagate outer tensor constraints to inner tensors if not already present
        for attr in attrs:
            match getattr(t, attr):
                case torch.Tensor() as inner_value:
                    inner_source = AttrSource(source, attr)
                    inner_contexts[attr] = _create_symbolic_context_for_tensor(
                        inner_value, inner_source, t_constraints, sources, mode
                    )
                case OpaqueBase():
                    pass
                case unexpected:
                    raise AssertionError(
                        f"expected Tensor or OpaqueBase, got {type(unexpected)}"
                    )

        symbolic_context = SubclassSymbolicContext(
            dynamic_sizes=dynamic_sizes,
            constraint_sizes=constraint_sizes,  # type: ignore[arg-type]
            view_base_context=None,
            tensor_source=source,
            shape_env_to_source_to_symbol_cache={},
            inner_contexts=inner_contexts,
        )
    else:
        symbolic_context: StatelessSymbolicContext = (  # type: ignore[no-redef]
            StatelessSymbolicContext(
                dynamic_sizes=dynamic_sizes,
                constraint_sizes=constraint_sizes,  # type: ignore[arg-type]
            )
        )

    # Apply constraints (common logic)
    t_id = id(t)
    if mode.shape_env is None:
        raise AssertionError("mode.shape_env must not be None")
    if t_id in t_constraints:
        for i, constraint in t_constraints[t_id].items():
            src = TensorPropertySource(base=source, prop=TensorProperty.SIZE, idx=i)
            sources[(t_id, i)].append(src)
            if isinstance(constraint, _RelaxedConstraint):
                continue
            symbolic_context.constraint_sizes[i] = constraint.constraint_range
            mode.shape_env.source_name_to_debug_name[src.name] = constraint.name  # type: ignore[assignment]

    return symbolic_context