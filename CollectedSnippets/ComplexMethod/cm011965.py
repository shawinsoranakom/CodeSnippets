def _aoti_flatten_inputs(
    gm: torch.fx.GraphModule,
    args: list[Any] | tuple[Any, ...],
    kwargs: dict[str, Any] | None = None,
    *,
    options: dict[str, Any] | None = None,
) -> tuple[list[Any], dict[str, Any]]:
    """
    Flatten the inputs to the graph module and return the flat inputs and options.
    Add "aot_inductor.serialized_in_spec" and "aot_inductor.serialized_out_spec" to the options.
    """
    # pyrefly: ignore [missing-module-attribute]
    from .compile_fx import graph_returns_tuple

    assert graph_returns_tuple(gm), (
        "Graph output must be a tuple(). This is so that we can avoid "
        "pytree processing of the outputs. Please change the module to "
        "have tuple outputs."
    )

    # We will serialize the pytree info into the .so as constant strings
    in_spec = None
    out_spec = None
    if isinstance(gm.graph._codegen, torch.fx.graph._PyTreeCodeGen):
        codegen = gm.graph._codegen
        gm.graph._codegen = torch.fx.graph.CodeGen()
        gm.recompile()

        if codegen.pytree_info.in_spec is not None:
            in_spec = codegen.pytree_info.in_spec
        if codegen.pytree_info.out_spec is not None:
            out_spec = codegen.pytree_info.out_spec

    else:
        if hasattr(gm, "_in_spec"):
            in_spec = gm._in_spec
        if hasattr(gm, "_out_spec"):
            out_spec = gm._out_spec

    serialized_in_spec = pytree.treespec_dumps(in_spec) if in_spec is not None else ""
    serialized_out_spec = (
        pytree.treespec_dumps(out_spec) if out_spec is not None else ""
    )

    flat_args_with_path, received_spec = pytree.tree_flatten_with_path(
        (args, kwargs or {})
    )

    if any(isinstance(x[1], torch.ScriptObject) for x in flat_args_with_path):
        from torch._dynamo.exc import UserError, UserErrorType

        raise UserError(
            UserErrorType.INVALID_INPUT,
            "TorchBind objects found in inputs. TorchBind object inputs are not supported in AOTInductor. "
            "TorchBind objects can only be attributes.",
        )

    # Replace non-tensor (constant) inputs with Nones, since these are not being
    # used anyways by the graph
    flat_example_inputs = [
        x[1] if isinstance(x[1], torch.Tensor) else None for x in flat_args_with_path
    ]

    if in_spec is not None and received_spec != in_spec:
        raise ValueError(
            "Trying to flatten user inputs with exported input tree spec: \n"
            f"{in_spec}\n"
            "but actually got inputs with tree spec of: \n"
            f"{received_spec}"
        )

    options = (
        {
            "aot_inductor.serialized_in_spec": serialized_in_spec,
            "aot_inductor.serialized_out_spec": serialized_out_spec,
        }
        if options is None
        else {
            **options,
            "aot_inductor.serialized_in_spec": serialized_in_spec,
            "aot_inductor.serialized_out_spec": serialized_out_spec,
        }
    )
    return flat_example_inputs, options