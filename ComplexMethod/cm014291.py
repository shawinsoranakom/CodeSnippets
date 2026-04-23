def return_and_correct_aliasing(func, args, kwargs, out):
    """
    This function should be used by wrapper tensor ``__torch_dispatch__`` subclasses
    that would like to work with torch.compile. It ensures that the subclass
    properly implements the aliasing behavior of every op,
    which is needed for correctness in AOTAutograd.
    This function will handle:

        * When we see a view op, we will alias the storages of any
          input and output tensor subclasses

        * When we see an inplace or out= op, we will directly
          return the corresponding input tensor, instead of returning
          a (potentially) fresh output tensor.
    """

    # Caching here because torchgen parsing is definitely not fast, and this function is called
    # once for every op in the graph during functionalization.
    schema_info = get_alias_info(func)

    def get_arg_from_alias(output_alias, schema_info, args, kwargs):
        new_args, new_kwargs = torch.fx.operator_schemas.normalize_function(  # type: ignore[misc]
            func, args=args, kwargs=kwargs
        )

        arg_indices = [
            i for i, a in enumerate(schema_info.args) if output_alias in a.alias_set
        ]
        # For any dispatcher op with an output alias, we expect it to map to exactly one alias in the schema's input arguments.
        if len(arg_indices) != 1:
            raise AssertionError(
                "Expected exactly one argument index for the given output alias"
            )
        idx = arg_indices[0]
        arg_info = schema_info.args[idx]
        if arg_info.name is not None and arg_info.name in new_kwargs:
            return new_kwargs[arg_info.name]
        return new_args[idx]

    # Fix up the storages of any outs so that they point to the same storage as the input,
    # if func is a view op.
    _correct_storage_aliasing(
        func, schema_info, args, (out,) if not isinstance(out, tuple) else out
    )

    # For inplace_view ops in particular, we'll try hard to make sure that the wrapper subclass's
    # metadata is set correctly.
    if schema_info.is_inplace_view_op:
        # no_dispatch() to make sure that we secretly change the metadata on the wrapper,
        # but don't end up dispatching the op anywhere else.
        mutated_args = [
            x
            for i, x in enumerate(args)
            if _get_write_alias(schema_info.args[i]) is not None
        ]
        # Assumption: we have a very small number of inplace_view ops that follow a strict schema:
        # there is only a single argument that gets its metadata mutated.
        if len(mutated_args) != 1:
            raise AssertionError(
                "expected exactly one mutated arg for inplace_view ops"
            )
        # This check exists because we generally *do* want to update the metadata of any wrapper subclasses,
        # but FunctionalTensor is special: it overrides all size/stride calls to plumb to the inner tensor.
        # so we don't actually need to update the metadata (and attempting to do so causes errors)
        from torch._subclasses.functional_tensor import FunctionalTensor

        if not isinstance(mutated_args[0], FunctionalTensor):
            with torch.utils._mode_utils.no_dispatch():
                # See Note: [Fake Tensor Dispatch Keys]
                # we're borrowing the way it modifies dispatch key TLS.
                meta_in_tls = torch._C._meta_in_tls_dispatch_include()
                torch._C._set_meta_in_tls_dispatch_include(True)
                try:
                    func(*args, **kwargs)
                finally:
                    torch._C._set_meta_in_tls_dispatch_include(meta_in_tls)

    # Next: we need to make sure to return inputs directly, if the output is a mutable alias (e.g. add_()).

    schema_info_outs_write_aliases = schema_info.outs_write_aliases
    # simple case: none of our outputs have mutable aliases, so we can return the output as-is
    if schema_info_outs_write_aliases is None:
        return out

    if len(schema_info_outs_write_aliases) == 1:
        return get_arg_from_alias(
            schema_info_outs_write_aliases[0], schema_info, args, kwargs
        )

    # In the multi-return case, all aten ops return a tuple / list, so cast accordingly.
    outs_to_return = type(out)(
        [
            (get_arg_from_alias(write_alias, schema_info, args, kwargs))
            for write_alias in schema_info_outs_write_aliases
        ]
    )
    return outs_to_return