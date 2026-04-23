def mark_unbacked(
    t: Any,
    index: int | list[Any] | tuple[Any],
    hint_override: int | None = None,
    strict: bool = False,
    specialize_on: list[Any] | None = None,
    shape_id: str | None = None,
    min: int | None = None,
    max: int | None = None,
) -> None:
    """
    Mark a tensor as having an unbacked dimension. This changes the semantics of operations:
    - The size of the specified dimension will always be reported as not equal to zero or one.
    - Assertions on this index will be turned into runtime asserts.
    - Attempting to get the real value of this dimension will raise an exception.
    - In effect, this dimension is treated as data-dependent (its value is unknown).

    Args:
        t (Any): The tensor to mark as having an unbacked dimension.
        index (int or list/tuple of int): The dimension(s) to mark as unbacked. Can be a single integer or a list/tuple of integers.
        hint_override (Optional[int], default=None): An optional integer to override the size hint for this dimension.
            This is only used by the inductor backend for size hint queries, such as during autotuning.
            NOTE: changing hint_override values will cause FxGraphCache misses, since hint overrides
            affect inductor codegen decisions and are included in the cache key via
            ShapeEnv.var_to_hint_override.
        strict (bool, default=False): If True, an error will be raised if the unbacked dimension is specialized.
            By default (strict=False), specialization is allowed and will proceed without error.
        specialize_on (Optional[list[Any]], default=None): A list of specialization criteria (e.g., lambdas) for this dimension.
            If provided, Dynamo will generate specialized compiled regions for each criterion in addition to a generic trace.
        shape_id (Optional[str], default=None): An optional identifier to group unbacked dimensions together.
            All unbacked dimensions with the same shape_id will share the same unbacked symbol. This is useful when multiple tensors
            are known to have the same batch size at runtime. A runtime assertion is added
            to ensure this property at runtime.
        min (Optional[int], default=None): Minimum value constraint for this dimension.
            If provided, a runtime check will be added to ensure the dimension is >= min.
        max (Optional[int], default=None): Maximum value constraint for this dimension.
            If provided, a runtime check will be added to ensure the dimension is <= max.
    """
    if torch.distributed.is_available() and isinstance(
        t, torch.distributed.tensor.DTensor
    ):
        # apply on inner tensor sizes/strides
        mark_unbacked(t._local_tensor, index, shape_id=shape_id)
    else:
        # You could have copied the mark_dynamic behavior but I'm not convinced
        # it's what you want
        assert not is_traceable_wrapper_subclass(t), "not implemented yet"

    if isinstance(index, int):
        if strict:
            if not hasattr(t, "_dynamo_strict_unbacked_indices"):
                t._dynamo_strict_unbacked_indices = set()

            t._dynamo_strict_unbacked_indices.add(index)
            return

        if not hasattr(t, "_specialized_on"):
            # pyrefly: ignore [implicit-any]
            t._specialize_on = {}

        if not hasattr(t, "_dynamo_unbacked_indices"):
            t._dynamo_unbacked_indices = set()

        if not hasattr(t, "_dynamo_hint_overrides"):
            # pyrefly: ignore [implicit-any]
            t._dynamo_hint_overrides = {}

        if hint_override:
            t._dynamo_hint_overrides[index] = hint_override

        if min is not None or max is not None:
            if not hasattr(t, "_dynamo_unbacked_bounds"):
                # pyrefly: ignore [implicit-any]
                t._dynamo_unbacked_bounds = {}
            t._dynamo_unbacked_bounds[index] = (min, max)

        if shape_id is not None:
            if not hasattr(t, "_dynamo_shape_ids"):
                # pyrefly: ignore [implicit-any]
                t._dynamo_shape_ids = {}
            t._dynamo_shape_ids[index] = shape_id

        # FX tracers don't respect @forbid_in_graph and choke on the following error since it passes in proxies:
        # TypeError: 'Attribute' object does not support item assignment

        if isinstance(t._specialize_on, dict):
            t._specialize_on[index] = specialize_on if specialize_on is not None else []

        t._dynamo_unbacked_indices.add(index)
        return

    assert isinstance(index, (list, tuple))
    for i in index:
        mark_unbacked(t, i, shape_id=shape_id, min=min, max=max)