def is_supported(g: NativeFunctionsGroup | NativeFunctionsViewGroup) -> bool:
    base_op_name = ""
    func = None
    if isinstance(g, NativeFunctionsViewGroup):
        base_op_name = g.view.root_name
        func = g.view.func
    else:
        base_op_name = g.out.func.name.name.base
        func = g.out.func
    if config.is_hand_written(g):
        logger.info("HAND WRITTEN: %s", base_op_name)
        return False
    if base_op_name in BLOCKED_OPS:
        logger.info("BLOCKED: %s", base_op_name)
        return False
    for arg in func.schema_order_arguments():
        maybe_method = ivalue_type_conversion_method(arg.type)
        if not maybe_method:
            # Type converting is unsupported yet.
            logger.info("NOT SUPPORTED TYPE CONVERTING: %s", func)
            return False

    if isinstance(g, NativeFunctionsViewGroup):
        # TODO: stop doing type tests by converting to C++ and then testing
        # the string, just test the dang thing directly
        if "at::Tensor" != cpp.returns_type(func.returns, symint=False).cpp_type():
            # Returns a non-Tensor value.
            logger.info("NON-TENSOR RET TYPE: %s", func)
            return False
        return True

    # For out variant ops, we need to check the arguments of its functional func.
    for arg in g.functional.func.schema_order_arguments():
        maybe_method = ivalue_type_conversion_method(arg.type)
        if not maybe_method:
            # Type converting is unsupported yet.
            logger.info("NOT SUPPORTED TYPE CONVERTING: %s", g.functional.func)
            return False

    if not g.structured:
        # In case of unstructured op, we check if it has out variant implementation.
        # The out variant implementation satisfies the minimum requirement that it has the output tensor as the last
        # parameter.
        if (
            not hasattr(g, "out")
            or not str(func).endswith("Tensor(a!) out) -> Tensor(a!)")
            or not str(func.name).endswith(".out")
        ):
            return False
    # TODO: stop type testing by converting to C++
    if "at::Tensor &" != cpp.returns_type(func.returns, symint=False).cpp_type():
        logger.info("NON_TENSOR RET TYPE: %s", func)
        return False
    if has_alias(func.arguments.non_out):
        # This op may create an alias of inputs.
        logger.info("INPUTS ALIAS: %s", base_op_name)
        return False
    return True