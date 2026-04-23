def _check_and_unexpand_args(func, expanded_args, expanded_kwargs):
    # input must be the first argument passed
    input = expanded_args[0]
    if isinstance(input, ExpandedWeight):
        raise RuntimeError(
            "Expanded Weights do not support inputs that are also ExpandedWeights. "
            f"Input must be a Tensor, got {type(input).__name__} in function {func.__name__}"
        )
    if not isinstance(input, torch.Tensor):
        raise RuntimeError(
            "Expanded Weights requires a Tensor as the first input to get the batch dimension, "
            f"got {type(input).__name__} in function {func.__name__}"
        )
    if len(input.shape) == 0:
        raise RuntimeError(
            f"Expanded Weights requires a batch dimension but got an input of size 0 in function {func.__name__}"
        )
    if input.shape[0] == 0:
        raise RuntimeError(
            "0 is not a valid batch size for Expanded Weights but got input tensor of "
            f"{input} in function {func.__name__}"
        )
    for arg in expanded_args + tuple(expanded_kwargs.values()):
        if not isinstance(arg, ExpandedWeight):
            continue
        batch_size = input.shape[0] if arg.batch_first else input.shape[1]
        if (arg.allow_smaller_batches and batch_size > arg.batch_size) or (
            not arg.allow_smaller_batches and arg.batch_size != batch_size
        ):
            raise RuntimeError(
                "Expected ExpandedWeights to have batch size matching input but got "
                f"input batch size of {batch_size} with ExpandedWeight of batch size {arg.batch_size}"
            )

    loss_reduction: str | None = None
    for arg in expanded_args + tuple(expanded_kwargs.values()):
        if isinstance(arg, ExpandedWeight):
            if loss_reduction is None:
                loss_reduction = arg.loss_reduction
            elif loss_reduction != arg.loss_reduction:
                raise RuntimeError(
                    "Expected ExpandedWeights to all have the same loss_reduction argument but got one"
                    f"with {loss_reduction} and one with {arg.loss_reduction}"
                )

    unexpanded_args = tuple(
        arg.orig_weight if isinstance(arg, ExpandedWeight) else arg
        for arg in expanded_args
    )
    unexpanded_kwargs = {
        name: arg.orig_weight if isinstance(arg, ExpandedWeight) else arg
        for (name, arg) in expanded_kwargs.items()
    }
    return unexpanded_args, unexpanded_kwargs