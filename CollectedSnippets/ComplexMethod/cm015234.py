def generate_vmap_inputs(
    arg_values, kwarg_values, is_batch_norm_and_training=False, batch_size=2
):
    flat_args, arg_spec = pytree.tree_flatten(tuple(arg_values))
    is_tensors = [isinstance(a, torch.Tensor) for a in flat_args]
    num_tensors = sum(is_tensors)
    # For Batch Norm, if there's only an input, we can't
    # batch it since running_mean/var will be seen as unbatched tensors
    if num_tensors == 1 and is_batch_norm_and_training:
        return
    bdim_choices = (
        get_bdim_choices_batch_norm(num_tensors, *arg_values)
        if is_batch_norm_and_training
        else get_bdim_choices(num_tensors)
    )

    @memoize
    def get_batched_arg(arg, bdim):
        if not isinstance(arg, torch.Tensor):
            raise AssertionError(f"Expected arg to be a torch.Tensor, got {type(arg)}")
        if bdim is None:
            raise AssertionError("Expected bdim to not be None")
        result, _ = add_batch_dim(arg, bdim, batch_size)
        return result

    for bdim_choice in bdim_choices:
        flat_in_dims = construct_in_dims(bdim_choice, is_tensors)

        flat_batched_args = tuple(
            arg if in_dim is None else get_batched_arg(arg, in_dim)
            for arg, in_dim in zip(flat_args, flat_in_dims)
        )
        batched_args = pytree.tree_unflatten(flat_batched_args, arg_spec)
        in_dims = pytree.tree_unflatten(flat_in_dims, arg_spec)
        yield batched_args, in_dims, kwarg_values