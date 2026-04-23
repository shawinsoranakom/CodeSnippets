def validate_subgraph_output_types(
    output: VariableTracker | Sequence[VariableTracker],
) -> None:
    """Verify that the output of the subgraph is a tensor,
    int, bool, SymBool, or SymInt.
    """
    from . import TensorVariable

    if non_tensor_output := find_mismatched_vars(
        output, TensorVariable, allow_none=True
    ):
        for out in non_tensor_output:
            if (
                (isinstance(out, SymNodeVariable) and out.python_type() in (int, bool))
                or (
                    out.is_python_constant()
                    and isinstance(out.as_python_constant(), (int, bool))
                )
                or isinstance(out, TorchScriptObjectVariable)
            ):
                continue
            unimplemented(
                gb_type="HOP body output unsupported",
                context=f"non-tensor outputs: {non_tensor_output}",
                explanation="HigherOrderOperator body's output must consist of tensors or ints/bools only "
                f"but got {out.python_type()}.",
                hints=[
                    *graph_break_hints.USER_ERROR,
                ],
            )