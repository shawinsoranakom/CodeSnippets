def _convert_guards_to_code(graph_module):
    shape_env = _get_shape_env(graph_module)
    if shape_env is None:
        return []

    local_vars = {
        var
        for var, sources in shape_env.var_to_sources.items()
        if all(
            not isinstance(source, torch._dynamo.source.ConstantSource)
            for source in sources
        )
    }
    py_printer = torch.fx.experimental.symbolic_shapes.ShapeGuardPythonPrinter(
        shape_env.var_to_sources, lambda s: s.name, shape_env.var_to_sources
    )
    ret = [
        py_printer.doprint(guard.expr)
        for guard in shape_env.guards
        if guard.expr.free_symbols.issubset(local_vars)
    ]
    # TODO Figure out how to resolve guards containing weight sizes.
    # This is not a big deal as _guards_code is mostly empty today.
    return [guard for guard in ret if "L['self']" not in guard]