def unpack_args(f: NativeFunction) -> tuple[list[str], list[Binding]]:
    body: list[str] = []
    unpacked_bindings: list[Binding] = []

    for i, binding in enumerate(extract_bindings(f)):
        if isinstance(binding.argument, SelfArgument):
            raise AssertionError("Binding argument should not be SelfArgument")
        if isinstance(binding.argument, TensorOptionsArguments):
            raise RuntimeError("VariableKernel shouldn't take TensorOptions")

        is_nullable = binding.argument.type.is_nullable()
        if not binding.argument.type.is_tensor_like() or is_nullable:
            unpacked_bindings.append(binding)
            continue

        is_tensor_list = is_tensor_list_type(binding.argument.type)
        ref = (not is_nullable) and not is_tensor_list
        suffix = "_opt" if is_nullable and not is_tensor_list else ""
        body.append(
            UNPACK_TENSOR.substitute(
                arg_name=binding.name,
                arg_pos=i,
                suffix=suffix,
                ref="&" if ref else "",
            )
        )
        unpacked_bindings.append(
            Binding(
                name=unpacked_name(binding.name),
                nctype=binding.nctype,
                argument=binding.argument,
                default=binding.default,
            )
        )

    return body, unpacked_bindings