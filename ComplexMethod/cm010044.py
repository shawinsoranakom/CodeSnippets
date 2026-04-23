def _create_batched_inputs(
    in_dims: in_dims_t,
    args: tuple,
    vmap_level: int,
    func: Callable,
) -> tuple[tuple, int]:
    if not isinstance(in_dims, int) and not isinstance(in_dims, tuple):
        raise ValueError(
            f"vmap({_get_name(func)}, in_dims={in_dims}, ...)(<inputs>): "
            f"expected `in_dims` to be int or a (potentially nested) tuple "
            f"matching the structure of inputs, got: {type(in_dims)}."
        )
    if len(args) == 0:
        raise ValueError(
            f"vmap({_get_name(func)})(<inputs>): got no inputs. Maybe you forgot to add "
            f"inputs, or you are trying to vmap over a function with no inputs. "
            f"The latter is unsupported."
        )

    flat_args, args_spec = tree_flatten(args)
    flat_in_dims = _broadcast_to_and_flatten(in_dims, args_spec)
    if flat_in_dims is None:
        raise ValueError(
            f"vmap({_get_name(func)}, in_dims={in_dims}, ...)(<inputs>): "
            f"in_dims is not compatible with the structure of `inputs`. "
            f"in_dims has structure {tree_flatten(in_dims)[1]} but inputs "
            f"has structure {args_spec}."
        )

    for arg, in_dim in zip(flat_args, flat_in_dims):
        if not isinstance(in_dim, int) and in_dim is not None:
            raise ValueError(
                f"vmap({_get_name(func)}, in_dims={in_dims}, ...)(<inputs>): "
                f"Got in_dim={in_dim} for an input but in_dim must be either "
                f"an integer dimension or None."
            )
        if isinstance(in_dim, int) and not isinstance(arg, Tensor):
            raise ValueError(
                f"vmap({_get_name(func)}, in_dims={in_dims}, ...)(<inputs>): "
                f"Got in_dim={in_dim} for an input but the input is of type "
                f"{type(arg)}. We cannot vmap over non-Tensor arguments, "
                f"please use None as the respective in_dim"
            )
        if in_dim is not None and (in_dim < 0 or in_dim >= arg.dim()):
            raise ValueError(
                f"vmap({_get_name(func)}, in_dims={in_dims}, ...)(<inputs>): "
                f"Got in_dim={in_dim} for some input, but that input is a Tensor "
                f"of dimensionality {arg.dim()} so expected in_dim to satisfy "
                f"0 <= in_dim < {arg.dim()}."
            )

    batch_size = _validate_and_get_batch_size(flat_in_dims, flat_args)
    # See NOTE [Ignored _remove_batch_dim, _add_batch_dim]
    batched_inputs = [
        arg if in_dim is None else torch._add_batch_dim(arg, in_dim, vmap_level)
        for in_dim, arg in zip(flat_in_dims, flat_args)
    ]
    return tree_unflatten(batched_inputs, args_spec), batch_size