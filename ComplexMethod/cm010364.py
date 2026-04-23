def call_op(op: OpOverload | HopInstance, args, kwargs):
    if isinstance(op, OpOverload):
        return op(*args, **kwargs)

    if not isinstance(op, HopInstance):
        raise AssertionError(f"Expected HopInstance, got {type(op)}")
    schema = op._schema
    bound_args = list(args)
    bound_kwargs = {}
    for arg in schema.arguments[len(bound_args) :]:
        if arg.name not in kwargs:
            raise AssertionError(f"arg {arg.name} not in kwargs: {kwargs}")
        val = kwargs[arg.name]
        if not arg.kwarg_only:
            bound_args.append(val)
        else:
            bound_kwargs[arg.name] = val

    if schema.tree_spec is not None:
        if len(bound_args) != len(schema.arguments) or len(bound_kwargs) != 0:
            raise AssertionError(
                f"Expected {len(schema.arguments)} bound_args and 0 bound_kwargs, "
                f"got {len(bound_args)} and {len(bound_kwargs)}"
            )
        args, kwargs = pytree.tree_unflatten(bound_args, schema.tree_spec)
        return op(*args, **kwargs)
    else:
        if len(bound_args) + len(bound_kwargs) != len(schema.arguments):
            raise AssertionError(
                f"Expected {len(schema.arguments)} total args, "
                f"got {len(bound_args)} + {len(bound_kwargs)}"
            )
        return op(*bound_args, **bound_kwargs)