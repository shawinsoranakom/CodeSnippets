def generate_out_variant_call(
    g: NativeFunctionsGroup, backend_index: BackendIndex
) -> str:
    schema = g.out.func
    if not schema.is_out_fn():
        raise AssertionError(f"Expected out function, got {schema}")
    arg_names = []
    kernel_name = get_out_kernel_name(g, backend_index)
    if g.structured:
        # structured op starts with the output tensor argument.
        arg_names = [out_arg.name for out_arg in schema.arguments.out]
    else:
        arg_names = []
    for arg in schema.arguments.non_out:
        if isinstance(arg, SelfArgument):
            arg_names.append(arg.argument.name)
        else:
            if not isinstance(arg, Argument):
                raise AssertionError(f"Expected Argument, got {type(arg)}")
            arg_names.append(arg.name)
    if not g.structured:
        if len(schema.arguments.out) != 1:
            raise AssertionError(
                f"Expected 1 out argument, got {len(schema.arguments.out)}"
            )
        arg_names.append(schema.arguments.out[0].name)
    cpp_arg_names = ",".join(arg_names)
    namespace_name = "cpu" if g.structured else "native"
    return f"at::{namespace_name}::{kernel_name}({cpp_arg_names})"