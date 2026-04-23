def _format_model_info(model_info: ModelInfo) -> str:
    """Format the information about the model."""
    lines = [
        textwrap.dedent(
            f"""\
            PyTorch ONNX Conversion Analysis

            ## Model Information

            The model has {sum(model_info.parameter_count.values())} parameters and {sum(model_info.buffer_count.values())} buffers (non-trainable parameters).
            Number of parameters per dtype:
            ```python
            {model_info.parameter_count}
            ```
            Number of buffers per dtype:
            ```python
            {model_info.buffer_count}
            ```
            """
        ),
        "Inputs:",
        *[f"- `{name}`: `{meta}`" for name, meta in model_info.inputs.items()],
        "",
        "Outputs:",
        *[f"- `{name}`: `{meta}`" for name, meta in model_info.outputs.items()],
        "",
        f"The FX graph has {model_info.fx_node_count} nodes in total. Number of FX nodes per op:",
    ]
    for op, count in model_info.fx_node_op_count.items():
        lines.append(f"- `{op}`: {count}")
    lines.append("\n")
    lines.append("Of the call_function nodes, the counts of operators used are:\n")
    sorted_targets = sorted(
        model_info.fx_node_target_count.items(),
        key=operator.itemgetter(1),
        reverse=True,
    )
    for target, count in sorted_targets:
        lines.append(f"- `{target}`: {count}")

    lines.append("")
    lines.append("## ONNX Conversion Information")
    lines.append("")

    if model_info.dispatch_failures:
        lines.append(
            "The model contains operators the dispatcher could not find registered ONNX decompositions for. "
            "This may be due to missing implementations, decompositions not registered "
            "correctly, or a bug in the dispatcher."
        )
        lines.append("")
        lines.append("Errors grouped by operator:\n")

        target_to_nodes = defaultdict(list)
        for node, _ in model_info.dispatch_failures:
            target_to_nodes[str(node.target)].append(node)

        target_to_messages = {}
        for node, message in model_info.dispatch_failures:
            if str(node.target) not in target_to_messages:
                target_to_messages[str(node.target)] = message

        for target, nodes in sorted(
            target_to_nodes.items(), key=operator.itemgetter(0), reverse=True
        ):
            message = textwrap.indent(
                f"{target_to_messages[target]}. Example node: `{nodes[0].format_node()}`. All nodes: `{nodes}`",
                "    ",
            )
            lines.append(f"- `{target}`: {message}")
    else:
        lines.append("All operators in the model have registered ONNX decompositions.")

    return "\n".join(lines)