def _gen_unsupported_methods_properties():
    tensor_attrs = set(filter(lambda x: x[0] != "_", dir(torch.Tensor)))
    tensor = torch.tensor([2])
    funcs_template = dedent(
        """
    def func(x):
        return x.{op}()
    """
    )

    deprecated_apis = {
        "volatile",
        "resize",
        "reinforce",
        "new",
        "name",
        "map2_",
        "has_names",
        "grad_fn",
        "resize_as",
    }
    tensor_attrs = tensor_attrs - deprecated_apis

    properties = []
    methods = []
    sorted_tensor_attrs = sorted(tensor_attrs, key=lambda x: x.lower())
    for attr in sorted_tensor_attrs:
        funcs_str = funcs_template.format(op=attr)
        scope: dict[str, Any] = {}
        execWrapper(funcs_str, globals(), scope)
        try:
            torch.jit.CompilationUnit(funcs_str)
        except Exception as e:
            if "nonexistent attribute" not in repr(e):
                continue
            attr_repr = repr(getattr(tensor, attr))
            if "bound method" in attr_repr or "built-in method" in attr_repr:
                methods.append(attr)
            else:
                properties.append(attr)

    mapped_methods = ("\t*  :meth:`~torch.Tensor." + x + r"`" for x in methods)
    mapped_properties = ("\t*  :attr:`~torch.Tensor." + x + r"`" for x in properties)
    return "\n".join(mapped_methods), "\n".join(mapped_properties)