def normalize_function(
    target: Callable[..., Any],
    args: tuple[Any, ...],
    kwargs: dict[str, Any] | None = None,
    arg_types: tuple[Any] | None = None,
    kwarg_types: dict[str, Any] | None = None,
    normalize_to_only_use_kwargs: bool = False,
) -> ArgsKwargsPair | None:
    """
    Returns normalized arguments to PyTorch functions. This means that
    `args/kwargs` will be matched up to the functional's
    signature and return exclusively kwargs in positional order if
    `normalize_to_only_use_kwargs` is True.
    Also populates default values. Does not support positional-only
    parameters or varargs parameters (*args, **kwargs). Does not support modules.

    May require `arg_types` and `kwarg_types` in order to disambiguate overloads.

    Args:
        target (Callable): Function that we are normalizing
        args (Tuple[Any]): Tuple of args to the function
        kwargs (Optional[Dict[str, Any]]): Dict of kwargs to the function
        arg_types (Optional[Tuple[Any]]): Tuple of arg types for the args
        kwarg_types (Optional[Dict[str, Any]]): Dict of arg types for the kwargs
        normalize_to_only_use_kwargs (bool): Whether to normalize to only use kwargs.

    Returns:

        Returns normalized_args_and_kwargs, or `None` if not successful.
    """
    if kwargs is None:
        kwargs = {}
    new_args_and_kwargs = None
    if (
        not isinstance(target, types.BuiltinFunctionType)
        and not (isinstance(target, (OpOverloadPacket, OpOverload)))
        and hasattr(target, "_op")
    ):
        # ExecuTorch's EdgeOpOverload are a wrapper around PyTorch's OpOverload,
        # so we can unwrap it here to get its schema
        # Can't import EdgeOpOverload directly because of a circular dependency,
        # so checking for "_op" existing is the next best thing.
        target = target._op

    # Repeat the condition after checking for the inner _op field.
    if not isinstance(target, types.BuiltinFunctionType) and not (
        isinstance(target, (OpOverloadPacket, OpOverload))
    ):
        target_for_analysis = target
        if target in boolean_dispatched:
            # HACK: `boolean_dispatch` as used in `torch.nn.functional` makes it so that we have
            # a 2-way dispatch based on a boolean value. Here we check that the `true` and `false`
            # branches of the dispatch have exactly the same signature. If they do, use the `true`
            # branch signature for analysis. Otherwise, leave this un-normalized
            if isinstance(target, str):
                raise AssertionError("target should not be a string here")
            dispatched = boolean_dispatched[target]
            if_true, if_false = dispatched["if_true"], dispatched["if_false"]
            if (
                inspect.signature(if_true).parameters
                != inspect.signature(if_false).parameters
            ):
                return None
            target_for_analysis = if_true

        if not callable(target_for_analysis):
            raise AssertionError(
                f"target_for_analysis must be callable, got {type(target_for_analysis)}"
            )
        sig = inspect.signature(inspect.unwrap(target_for_analysis))
        new_args_and_kwargs = _args_kwargs_to_normalized_args_kwargs(
            sig, args, kwargs, normalize_to_only_use_kwargs
        )
    else:
        if not callable(target):
            raise AssertionError(f"target must be callable, got {type(target)}")
        torch_op_schemas = get_signature_for_torch_op(target)
        matched_schemas: list[inspect.Signature] = []
        if torch_op_schemas:
            # Iterate through all of the schema until we find one that matches
            # If one matches, populate `new_args_and_kwargs` with the new args/kwargs
            # values. If none matches, `new_args_and_kwargs` will be None
            for candidate_signature in torch_op_schemas:
                try:
                    _fast_bind(candidate_signature, *args, **kwargs)
                    matched_schemas.append(candidate_signature)
                except TypeError:
                    continue

            if len(matched_schemas) == 0:
                # Did not match any schema. Cannot normalize
                pass
            elif len(matched_schemas) == 1:
                # Matched exactly one schema, unambiguous
                new_args_and_kwargs = _args_kwargs_to_normalized_args_kwargs(
                    matched_schemas[0], args, kwargs, normalize_to_only_use_kwargs
                )
            else:
                if arg_types is not None or kwarg_types is not None:
                    arg_types = arg_types if arg_types else cast(tuple[Any], ())
                    kwarg_types = kwarg_types if kwarg_types else {}
                    for candidate_signature in torch_op_schemas:
                        sig_matches = True
                        try:
                            bound_types = _fast_bind(
                                candidate_signature, *arg_types, **kwarg_types
                            )
                            for arg_name, arg_type in bound_types.arguments.items():
                                param = candidate_signature.parameters[arg_name]
                                sig_matches = sig_matches and type_matches(
                                    param.annotation, arg_type
                                )
                        except TypeError:
                            sig_matches = False
                        if sig_matches:
                            new_args_and_kwargs = (
                                _args_kwargs_to_normalized_args_kwargs(
                                    candidate_signature,
                                    args,
                                    kwargs,
                                    normalize_to_only_use_kwargs,
                                )
                            )
                            break
                else:
                    # Matched more than one schema. In this situation, the caller must provide the types of
                    # the arguments of the overload they expect.
                    schema_printouts = "\n".join(
                        str(schema) for schema in matched_schemas
                    )
                    raise RuntimeError(
                        f"Tried to normalize arguments to {torch.typename(target)} but "
                        f"the schema match was ambiguous! Please provide argument types to "
                        f"the normalize_arguments() call. Available schemas:\n{schema_printouts}"
                    )

    return new_args_and_kwargs