def constrain_to_fake_tensor(arg, fake_arg):
    if fake_arg is None:
        return arg
    if isinstance(fake_arg, FakeScriptObject) or is_opaque_value(fake_arg):
        return arg
    if isinstance(arg, ir.IRNode):
        return ir.ExternKernel.require_exact_strides(arg, fake_arg.stride())
    if isinstance(arg, dict):
        return {key: constrain_to_fake_tensor(arg[key], fake_arg[key]) for key in arg}
    elif isinstance(arg, (tuple, list)):
        return type(arg)(
            constrain_to_fake_tensor(a, f_a) for (a, f_a) in zip(arg, fake_arg)
        )
    return arg