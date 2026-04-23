def _get_fake_value_impl(
    node: torch.fx.Node,
    tx: InstructionTranslatorBase,
    allow_non_graph_fake: bool = False,
) -> Any:
    """
    Run the computation represented by `node` using fake tensors and return the result.

    allow_non_graph_fake: whether to allow the return result to be:
        1. non-fake or 2. fake that is not created by this instance of Dynamo.
        If `True`, you must be prepared to deal with such return values, ideally
        by further wrapping them as this graph's fakes.
    """
    from torch.utils._sympy.value_ranges import ValueRangeError

    from . import graph_break_hints
    from .exc import unimplemented, Unsupported, UserError, UserErrorType

    op = node.op

    # FX Node should always return the same fake value
    if "example_value" in node.meta and is_fake(node.meta["example_value"]):
        return node.meta["example_value"]

    args, kwargs = get_fake_values_from_nodes(
        tx, (node.args, node.kwargs), allow_non_graph_fake
    )

    if (
        torch._dynamo.config.use_graph_deduplication
        or torch._dynamo.config.track_nodes_for_deduplication
    ):
        flat_args_kwargs = get_fake_values_from_nodes(
            tx, _get_flat_args(node, {}), allow_non_graph_fake
        )
        id_to_initial_version = {
            id(arg): arg._version for arg in flat_args_kwargs if is_fake(arg)
        }
    else:
        # pyrefly: ignore [implicit-any]
        flat_args_kwargs = []
        # pyrefly: ignore [implicit-any]
        id_to_initial_version = {}

    nnmodule = None
    fake_mode = tx.fake_mode
    assert fake_mode is not None
    if op == "call_method" and len(args) > 0 and isinstance(args[0], torch.nn.Module):
        # If the first argument is nn.Module, should copy to fake mode.
        args = (deepcopy_to_fake_tensor(args[0], fake_mode),) + tuple(args[1:])

    if op == "call_module":
        nnmodule = tx.output.nn_modules[node.target]  # type: ignore[index]

        if is_lazy_module(nnmodule) and hasattr(nnmodule, "_initialize_hook"):
            # In the case of a lazy module, we want to run
            # the pre-hooks which initialize it.
            # Afterwards, lazy module deletes its pre-hooks
            # to avoid treating it as lazy on subsequent recompile.
            nnmodule._infer_parameters(nnmodule, args)

        # no matter it's lazy module or not, we should copy to fake mode.
        nnmodule = deepcopy_to_fake_tensor(nnmodule, fake_mode)

    if node.name in ["interpolate", "is_integer", "wrapped_gradient"] or any(
        isinstance(a, complex) for a in args
    ):
        # We need to specialize symfloats for now. Eventually we should do a tensorify pass in dynamo.
        args = tuple(
            (
                float(arg)
                if isinstance(arg, torch.SymFloat) and arg.node.hint is not None
                else arg
            )
            for arg in args
        )

    try:
        with fake_mode, enable_python_dispatcher():
            ret_val = wrap_fake_exception(
                lambda: run_node(tx.output, node, args, kwargs, nnmodule)
            )
    except Unsupported:
        raise
    except RuntimeError as e:
        cause: BaseException = e
        if e.__cause__ is not None:
            cause = e.__cause__

        if isinstance(
            cause, torch._subclasses.fake_tensor.DataDependentOutputException
        ):
            # capture_scalar_outputs only works for these ops right now
            # see torch/_subclasses/fake_impls.py
            if cause.func in (
                torch.ops.aten.item.default,
                torch.ops.aten._local_scalar_dense.default,
            ):
                # does this actually get triggered?
                hints = [
                    "Enable tracing of data-dependent output operators with "
                    "`torch._dynamo.config.capture_scalar_outputs = True`",
                ]
            else:
                hints = [
                    "Consider wrapping the operator into a PyTorch-understood custom operator "
                    "(see https://pytorch.org/tutorials/advanced/custom_ops_landing_page.html)",
                ]
            unimplemented(
                gb_type="Data dependent operator",
                context=str(cause.func),
                explanation=f"Operator `{cause.func}` has a non-Tensor output "
                "whose value is dependent on the data of Tensor inputs.",
                hints=hints,
                from_exc=cause,
            )
        elif isinstance(
            cause, torch._subclasses.fake_tensor.DynamicOutputShapeException
        ):
            if not torch._dynamo.config.capture_dynamic_output_shape_ops:
                unimplemented(
                    gb_type="Dynamic shape operator",
                    context=str(cause.func),
                    explanation=f"Operator `{cause.func}`'s output shape depends on input Tensor data.",
                    hints=[
                        "Enable tracing of dynamic shape operators with "
                        "`torch._dynamo.config.capture_dynamic_output_shape_ops = True`",
                    ],
                    from_exc=cause,
                )
            else:
                unimplemented(
                    gb_type="Dynamic shape operator (no meta kernel)",
                    context=str(cause.func),
                    explanation=f"Operator `{cause.func}` does not have a meta kernel that supports dynamic output shapes",
                    hints=[
                        "Please report an issue to PyTorch",
                    ],
                    from_exc=cause,
                )
        elif isinstance(
            cause, torch._subclasses.fake_tensor.UnsupportedOperatorException
        ):
            op = cause.func  # type: ignore[assignment]
            import_suggestion = ""
            if isinstance(op, torch._ops.OpOverload):
                maybe_pystub = torch._C._dispatch_pystub(
                    op._schema.name, op._schema.overload_name
                )
                if maybe_pystub is not None:
                    module, ctx = maybe_pystub
                    import_suggestion = (
                        f"It's possible that the support was implemented in "
                        f"module `{module}` and you may need to `import {module}`"
                        f"({ctx}), otherwise "
                    )
            unimplemented(
                gb_type="Operator does not support running with fake tensors",
                context=f"unsupported operator: {cause.func}",
                explanation="",
                hints=[
                    f"{import_suggestion}see "
                    "https://docs.google.com/document/d/1GgvOe7C8_NVOMLOCwDaYV1mXXyHMXY7ExoewHqooxrs/edit#heading=h.64r4npvq0w0"
                    " for how to fix",
                ],
                from_exc=cause,
            )
        elif isinstance(
            cause, torch.fx.experimental.symbolic_shapes.GuardOnDataDependentSymNode
        ):
            raise UserError(
                UserErrorType.CONSTRAINT_VIOLATION,
                str(cause),
                case_name="constrain_as_size_example",
            ) from cause
        elif isinstance(cause, ValueRangeError):
            raise UserError(UserErrorType.CONSTRAINT_VIOLATION, e.args[0]) from e
        elif isinstance(cause, TypeError) and "argument" in str(cause):
            unimplemented(
                gb_type="TypeError when making fake tensor call",
                context=f"TypeError {node.target}: {cause}",
                explanation="",
                hints=[*graph_break_hints.USER_ERROR],
                from_exc=cause,
            )
        msg = get_concrete_sizes_from_symints(str(e), fake_mode)
        _wrap_graph_break_with_torch_runtime_err(
            lambda: unimplemented(
                gb_type="RuntimeError when making fake tensor call",
                context="",
                explanation=msg,
                hints=[*graph_break_hints.USER_ERROR],
                from_exc=cause,
            )
        )
        raise AssertionError("should not reachable") from None

    if not allow_non_graph_fake:
        _ = pytree.tree_map_only(
            torch.Tensor, functools.partial(ensure_graph_fake, tx=tx), ret_val
        )

    if (
        torch._dynamo.config.use_graph_deduplication
        or torch._dynamo.config.track_nodes_for_deduplication
    ):
        tx.output.region_tracker.track_node_mutations(
            node,
            flat_args_kwargs,
            id_to_initial_version,
        )

    return ret_val