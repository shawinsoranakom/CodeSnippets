def cat(inputs, dim=0):
    """Lower aten.cat, choosing between pointwise_cat and ConcatKernel."""
    cpu_device = inputs[0].get_device().type == "cpu"
    if cpu_device and all(
        input.get_dtype() in [torch.int8, torch.uint8] for input in inputs
    ):
        # TODO <leslie> Remove this fallback when we support vectorization
        # code gen with uint8 data type directly.
        for input in inputs:
            input.realize()
        if all(len(input.get_size()) == 4 for input in inputs):
            inputs, _ = require_channels_last(aten.cat, *inputs)
        return fallback_handler(aten.cat.default)(inputs, dim)

    if len(inputs) == 1:
        return clone(inputs[0])

    dim = _validate_dim(inputs[0], dim, 0)
    dtype = get_promoted_dtype(
        *inputs, type_promotion_kind=ELEMENTWISE_TYPE_PROMOTION_KIND.DEFAULT
    )
    inputs = [to_dtype(inp, dtype) for inp in inputs]

    def unwrap_tensor(x: TensorBox | ir.StorageBox) -> ir.IRNode:
        if isinstance(x, TensorBox):
            if isinstance(x.data, ir.BaseView):
                return x.data.unwrap_view()
            else:
                return x.data

        if isinstance(x, ir.StorageBox):
            return x.data

        return x

    def is_reduction(t):
        return isinstance(t, ir.ComputedBuffer) and isinstance(t.data, ir.Reduction)

    def can_fuse_reduction(t, exclude: OrderedSet[str] = OrderedSet()):
        if isinstance(t, (TensorBox, ir.StorageBox)):
            return can_fuse_reduction(unwrap_tensor(t), exclude)
        return (
            is_reduction(t)
            or isinstance(t, ir.Pointwise)
            and any(
                read not in exclude
                and can_fuse_reduction(V.graph.get_buffer(read), exclude)
                for read in t.get_read_names()
            )
        )

    # Pointwise cat evaluates every input's computation for each
    # output element (masked), so fusing reductions in is wasteful.
    # Exception: when inputs just recombine a reduction's output
    # (e.g. qknorm → RoPE → cat), we do not duplicate computation
    recombined = _cat_inputs_recombine_reduction(inputs, dim)
    exclude: OrderedSet[str] = OrderedSet([recombined]) if recombined else OrderedSet()
    fusable_reduction = any(can_fuse_reduction(t, exclude) for t in inputs)

    def should_lower_cat_input(x) -> bool:
        # Unrealized inputs will not be storage and layouts, and we dont want to realize
        # them in case we want to fuse
        if ir.is_storage_and_layout(x):
            storage, _ = ir.as_storage_and_layout(x, freeze=False)
            return not ir.ConcatKernel.can_realize_into_without_copy(storage)

        if isinstance(x, (TensorBox, ir.StorageBox)):
            return should_lower_cat_input(unwrap_tensor(x))

        if isinstance(x, ir.Pointwise):
            return True

        return False

    if config.force_pointwise_cat:
        return pointwise_cat(inputs, dim)

    # TODO: We observed negative performance impact of pointwise_cat optimization on CPU so disabled it.
    #             We will revisit this later after enabling vectorization on index_expr.
    if cpu_device:
        return TensorBox(ir.ConcatKernel.create(inputs, dim))

    def op_count(x):
        if isinstance(x, (TensorBox, ir.StorageBox)):
            return op_count(unwrap_tensor(x))

        # this will correspond to a direct memory read
        if not isinstance(x, ir.Pointwise):
            return 0

        count = x.inner_fn_opcount().num_ops
        for read in x.get_read_names():
            count += op_count(V.graph.get_buffer(read))

        return count

    # as of inputs increase, possibility for register spilling also increases
    # past a certain threshold of inputs we only fuse if the if the input kernels
    # are simple
    # not sure if we want to expose to users via config since logic may change in future
    MAX_COMPLEX_POINTWISE_CAT = 8
    MAX_SIMPLE_OP_COUNT = 2

    def additional_pointwise_ops(op: torch._ops.OpOverload):
        return op in (aten.cat.default, aten.constant_pad_nd.default)

    if len(inputs) <= MAX_COMPLEX_POINTWISE_CAT or (
        (len(inputs) <= config.max_pointwise_cat_inputs)
        and all(op_count(t) <= MAX_SIMPLE_OP_COUNT for t in inputs)
    ):
        pointwise_uses = all(
            is_pointwise_use(use, additional_pointwise_ops)
            for use in V.current_node.users
        )
        # fuse in case we will be used in a pointwise node, and there are any inputs we
        # we can prevent materialization of.
        fuse_pointwise_use = (
            any(should_lower_cat_input(inp) for inp in inputs) and pointwise_uses
        )

        # horizontal fuse in case all inputs will require a copy kernel anyway.
        # only horizontally fuse pointwise kernels

        # Skip pointwise_cat when any cat input has a fusible (pointwise)
        # multi-consumer — ConcatKernel + NonOwningLayout avoids redundant
        # reads. Also skip when input is an unrealized Pointwise with
        # multiple consumers to avoid recomputation (e.g. pad-as-cat).
        def any_input_has_multi_consumers() -> bool:
            current_node = V.current_node
            if current_node is None:
                return False
            fx_args = current_node.args[0]
            if isinstance(fx_args, (list, tuple)):
                input_nodes = fx_args
            elif isinstance(fx_args, torch.fx.Node):
                input_nodes = [fx_args]
            else:
                return False

            def is_unrealized_pointwise(x):
                if isinstance(x, (TensorBox, ir.StorageBox)):
                    return is_unrealized_pointwise(unwrap_tensor(x))
                return isinstance(x, ir.Pointwise)

            for arg, ir_input in zip(input_nodes, inputs):
                if not hasattr(arg, "users") or len(arg.users) <= 1:
                    continue
                # input will be computed multiple times because other consumers
                # (eg. pointwise) will also inline it. So we should realize-in-place via ConcatKernel
                if any(is_pointwise_use(u) for u in arg.users if u is not current_node):
                    return True
                # If input is an unrealized Pointwise with multiple consumers, pointwise_cat
                # will inline input without realizing it to memory, causing separate
                # realization cost for input. So we should realize-in-place via ConcatKernel
                if is_unrealized_pointwise(ir_input):
                    return True
            return False

        has_multi_consumers = any_input_has_multi_consumers()

        horizontal_fuse_cat = (
            all(should_lower_cat_input(inp) for inp in inputs) and not fusable_reduction
        )

        if not has_multi_consumers and (fuse_pointwise_use or horizontal_fuse_cat):
            return pointwise_cat(inputs, dim)

    return TensorBox(ir.ConcatKernel.create(inputs, dim))