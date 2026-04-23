def mark_dynamic(
    t: Any,
    index: int | list[Any] | tuple[Any],
    *,
    hint_override: int | None = None,
    min: int | None = None,
    max: int | None = None,
    specialize_on: list[Any] | None = None,
) -> None:
    """
    Mark a tensor as having a dynamic dim and set corresponding min and max range for the dim.

    [Note - on the state of mark_dynamic]

    The behavior of having a dynamic dimension on a tensor is governed by a few factors:

    1) torch._dynamo.config dynamic_shapes True or False.
        a) dynamic_shapes=True - dynamic_shapes must be True for mark_dynamic to work.
        a) dynamic_shapes=False - This config will raise an exception when used in conjunction with
        mark_dynamic. We will eventually support this.

    2) If the dimension is fully constrained - as in, it does not allow more than a single value
    in both eager (torch.compile, torch._dynamo.optimize) mode and export mode (torch._dynamo.export),
    we will raise an error

    3) If the dimension is partially constrained - allowing at least 2 values but not the full unbounded
    range of shapes, in eager we will pass it through, but export will raise an error.

    4) Attempts to trace this function will explicitly raise. As such, all calls to mark_dynamic must be made
    before torch.compile.

    5) If hint_override is passed, the hint_override for the specified dimension will replace the provided value
    from the first example input as the official size hint. Note: changing hint_override values will cause
    FxGraphCache misses, since hint overrides affect inductor codegen decisions (autotuning, reduction
    strategy, etc.) and are included in the cache key via ShapeEnv.var_to_hint_override.

    6) If specialize_on is passed in, we will perform a single generic Dynamo trace followed by
    multiple specialized compilations in addition to a single generic compilation. NB: For now we only support
    per dimension specialization, or in other words we do not generate a cross product of specializations.
    At runtime, we will dispatch to a specialized compiled region if the input matches the specialization criteria.

    For example:
        mark_dynamic(..., specialize_on=[
            lambda x: x == 8,
            lambda x: x == 16
        ])

    This approach results in one Dynamo trace and two backend compilations. When the input dimension equals 8 or 16
    at runtime, execution will be directed to the specialized compiled region. Performance measurements indicate
    2-8x speedups depending on the specific specialization and model architecture.

    """
    if is_traceable_wrapper_subclass(t):
        # default behavior: mirror mark_dynamic() on all inner tensors with same dim as t
        # TODO: Make this configurable via a supported public API
        _apply_func_to_inner_tensors_of_same_dim(
            mark_dynamic, t, index, min=min, max=max
        )

    if isinstance(index, int):
        if not hasattr(t, "_dynamo_dynamic_indices"):
            t._dynamo_dynamic_indices = set()

            t._dynamo_dynamic_range = set()

            # pyrefly: ignore [implicit-any]
            t._dynamo_hint_overrides = {}

        if not hasattr(t, "_specialize_on"):
            # pyrefly: ignore [implicit-any]
            t._specialize_on = {}

        if hint_override:
            t._dynamo_hint_overrides[index] = hint_override
        # TODO(voz): Should we bounds check?

        t._dynamo_dynamic_indices.add(index)
        t._dynamo_dynamic_range.add(_DimRange(index, min, max))  # type: ignore[arg-type]

        # FX tracers don't respect @forbid_in_graph and choke on the following error since it passes in proxies:
        # TypeError: 'Attribute' object does not support item assignment

        if isinstance(t._specialize_on, dict):
            t._specialize_on[index] = specialize_on if specialize_on is not None else []

        return

    assert isinstance(index, (list, tuple))
    for i in index:
        mark_dynamic(t, i, min=min, max=max)
        mark_dynamic(t, i, min=min, max=max, specialize_on=specialize_on)