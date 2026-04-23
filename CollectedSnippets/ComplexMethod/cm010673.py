def _get_nn_functional_ops():
    functions = []

    # Iterate over torch.nn.functional
    mod = torch.nn.functional
    name = mod.__name__
    for elem in dir(torch.nn.functional):
        attr = getattr(mod, elem)
        if not inspect.isfunction(attr) or _hidden(elem[0]):
            # Ignore non-functions and internal methods
            continue

        attr_module = inspect.getmodule(attr)
        if not attr_module:
            raise RuntimeError(f"Module for {attr} not found")

        if "torch.nn.functional" not in attr_module.__name__:
            # Ignore functions from outside torch.nn.functional
            continue

        try:
            # compile fn, get schema
            scripted = torch.jit.script(attr)
            scripted_schema = scripted.schema
            functions.append(_emit_schema(name, elem, scripted_schema))
        except:  # noqa: E722
            # Skip interpolate / boolean dispatched things
            pass

    # Iterate over modules that we know contain a lot of builtins
    for mod in torch.jit._builtins._modules_containing_builtins:
        name = mod.__name__
        for elem in dir(mod):
            builtin = _find_builtin(getattr(mod, elem))
            if builtin is not None:
                schemas = torch._C._jit_get_schemas_for_operator(builtin)
                for schema in schemas:
                    # remove _tan but not __and__
                    if not _hidden(elem):
                        functions.append(_emit_schema(name, elem, schema))
    return "Supported PyTorch Functions", functions