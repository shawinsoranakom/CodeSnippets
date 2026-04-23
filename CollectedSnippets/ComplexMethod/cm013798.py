def _extract_parameters_and_gradients(
    node: _ProfilerEvent,
) -> Iterator[tuple[TensorKey | None, TensorKey | None]]:
    children = node.children

    # AccumulateGrad is used in the Autograd engine to handle gradient updates.
    # There are two possible cases:
    # 1) This is a newly created gradient Tensor. In that case there is nothing
    #    to accumulate, so autograd simply detaches the Tensor.
    #
    # 2) There is a preexisting gradient Tensor and we need to add the newly
    #    computed update. This is done with an in-place add (aten::add_) op.
    #    (The underscore suffix denotes "in-place".)
    if (
        node.typed[0] == _EventType.TorchOp
        and node.typed[1].scope == RecordScope.BACKWARD_FUNCTION
        # TODO(robieta): Move away from load bearing names
        and node.name == "torch::autograd::AccumulateGrad"
        and children
        and children[0].typed[0] == _EventType.TorchOp
        and children[0].name in ("aten::detach", "aten::add_")
        and children[0].typed[1].inputs
        and isinstance(children[0].typed[1].inputs[0], _TensorMetadata)
    ):
        yield None, TensorKey.from_tensor(children[0].typed[1].inputs[0])

    # We directly instrument `torch.nn.Module` and `torch.optim.Optimizer`
    # NOTE: The values captured by the python tracer are cached; they can be
    #       used to build up labels but do not imply that a Tensor was live at
    #       a particular time.
    elif node.typed[0] == _EventType.PyCall:
        typed_fields = node.typed[1]
        if typed_fields.module is not None and typed_fields.optimizer is not None:
            raise AssertionError("module and optimizer cannot both be set")
        if typed_fields.module is not None:
            for _, p, p_grad in typed_fields.module.parameters:
                yield TensorKey.from_tensor(p), TensorKey.from_tensor(p_grad)

        if typed_fields.optimizer is not None:
            for p, p_grad, _ in typed_fields.optimizer.parameters:
                yield TensorKey.from_tensor(p), TensorKey.from_tensor(p_grad)