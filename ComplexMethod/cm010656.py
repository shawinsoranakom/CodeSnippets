def get_jit_class_def(cls, self_name):
    """Get definitions for each method within the current class independently.

    Args:
        cls: The class to get definition of.
        self_name: The name of the class that the properties should belong to.

    Returns:
        torch._C._jit_tree_views.ClassDef: A representation of the class,
            the methods in the class and their definition as a tree.
    """
    # TODO: proper overriding analysis when implementing class inheritance
    methods = inspect.getmembers(
        cls,
        predicate=lambda m: (inspect.ismethod(m) or inspect.isfunction(m))
        and not is_static_fn(cls, m.__name__)
        and m.__name__ in cls.__dict__
        and not _is_drop_fn(m),
    )

    def is_classmethod(fn):
        return inspect.ismethod(fn) and getattr(fn, "__self__", None) == cls

    # Get and parse the source code for this class
    sourcelines, file_lineno, filename = get_source_lines_and_file(
        cls, torch._C.ErrorReport.call_stack()
    )
    source = "".join(sourcelines)

    dedent_src = dedent(source)
    py_ast = ast.parse(dedent_src)

    class_ast = py_ast.body[0]
    if not isinstance(class_ast, ast.ClassDef):
        raise AssertionError(
            f"Expected class definition, got {type(class_ast).__name__}"
        )

    # Special case for dataclasses. In general we need access to the source code for
    # an object in order to JIT compile it. But the dataclasses module dynamically synthesizes
    # magic methods for classes, and we can't get the source code for these methods. As a
    # workaround, we synthesize TorchScript-friendly implementations ourselves.
    if dataclasses.is_dataclass(cls):
        # Detect whether the user manually implemented any of the magic methods. If they did,
        # we don't want to synthesize/override them.
        overrides = {
            method.name
            for method in class_ast.body
            if isinstance(method, ast.FunctionDef)
            and method.name in DATACLASS_MAGIC_METHODS
        }
        for i, (name, _) in enumerate(methods):
            # Is this a magic method we can synthesize?
            synthesizer_fn = DATACLASS_MAGIC_METHODS.get(name)
            if synthesizer_fn and name not in overrides:
                parsed_def = synthesizer_fn(cls)
                methods[i] = name, parsed_def
                func = getattr(cls, name)
                _jit_internal.loader.cache(func, parsed_def.source)

    method_defs = [
        get_jit_def(obj, name, self_name=self_name, is_classmethod=is_classmethod(obj))
        for (name, obj) in methods
    ]
    properties = get_class_properties(cls, self_name)

    leading_whitespace_len = len(source.split("\n", 1)[0]) - len(
        dedent_src.split("\n", 1)[0]
    )
    ctx = make_source_context(
        source, filename, file_lineno, leading_whitespace_len, False
    )
    assigns = get_class_assigns(ctx, class_ast)

    return build_class_def(ctx, class_ast, method_defs, properties, self_name, assigns)