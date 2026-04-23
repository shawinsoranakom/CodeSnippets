def get_jit_def(fn, def_name, self_name=None, is_classmethod=False):
    """
    Build a JIT AST (TreeView) from the given function.

    Args:
        fn: A function object to compile or a pre-parsed ParsedDef object
        def_name: The name to give to the resulting AST object. This is not
            always the same as `fn.__name__`, for example:
                def _forward(self):
                    ...
                forward = _forward
            In this case, the `__name__` attribute of the function object is "_forward",
            but we want the result AST to have the name "forward".
        self_name: If this function is a method, what the type name of `self` is.
    """
    parsed_def = parse_def(fn) if not isinstance(fn, _ParsedDef) else fn
    type_line = torch.jit.annotations.get_type_line(parsed_def.source)
    fn_def = parsed_def.ast.body[0]

    if is_classmethod:
        arg_name = fn_def.args.args[0].arg  # type:ignore[union-attr]
        # Insert a statement that assigns the first argument to the class
        assign_stmt = ast.parse(f"{arg_name} = {self_name}").body[0]
        fn_def.body.insert(0, assign_stmt)  # type:ignore[union-attr]

    # Swap out the function signature and body if it is unused
    if should_drop(fn):
        unused_fn_def = ast.parse(
            'def unused_fn(self: Any):\n\traise RuntimeError("Cannot call @unused methods")'
        )
        if len(unused_fn_def.body) != 1 or not isinstance(
            unused_fn_def.body[0], ast.FunctionDef
        ):
            raise RuntimeError(
                f"Expected a single top-level function: {parsed_def.filename}:{parsed_def.file_lineno}"
            )
        unused_def = unused_fn_def.body[0]
        fn_def.body = unused_def.body  # type:ignore[union-attr]
        # kwarg/vararg not supported by `build_def`
        fn_def.args.kwarg = fn_def.args.vararg = None  # type:ignore[union-attr]
        for arg in fn_def.args.args + fn_def.args.kwonlyargs:  # type:ignore[union-attr]
            # Replace potentially unsupported type annotations by "Any"
            arg.annotation = unused_def.args.args[0].annotation
        if _is_drop_fn(fn):
            # Dropping potentially unsupported return type annotation for jit._drop
            fn_def.returns = None  # type:ignore[union-attr]
            fn_def.type_comment = None  # type:ignore[union-attr]

    # If MonkeyType is installed, get all the consolidated type traces
    # for the arguments from type_trace_db
    type_trace_db = torch.jit._script._get_type_trace_db()
    pdt_arg_types = None
    if monkeytype_trace and not isinstance(fn, _ParsedDef):  # type: ignore[truthy-function]
        qualname = get_qualified_name(fn)
        pdt_arg_types = type_trace_db.get_args_types(qualname)

    return build_def(
        parsed_def.ctx,
        fn_def,
        type_line,
        def_name,
        self_name=self_name,
        pdt_arg_types=pdt_arg_types,
    )