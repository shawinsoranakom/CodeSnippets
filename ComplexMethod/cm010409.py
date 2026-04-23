def get_output_metadata(subgraph, *operands):
    """
    Extract metadata about the subgraph outputs WITHOUT executing the subgraph.
    This avoids running side-effectful operations twice (once here, once in forward).
    We analyze the graph structure statically to extract metadata.
    """
    # Unwrap FunctionalizeCtxWrapper if present
    if isinstance(subgraph, FunctionalizeCtxWrapper):
        subgraph = subgraph.subgraph

    # If not a GraphModule, fall back to execution-based metadata extraction
    if not isinstance(subgraph, torch.fx.GraphModule):
        return _get_output_metadata_by_execution(subgraph, *operands)

    output_metadata = OutputMetadata()

    # Extract output arguments from the output node
    # The output node has args=(output_values,) where output_values is a tuple/list
    output_node = next(reversed(subgraph.graph.find_nodes(op="output")))
    output_metadata.num_fw_outs = len(output_node.args[0])

    for idx, output_arg in enumerate(output_node.args[0]):
        if not isinstance(output_arg, torch.fx.Node):
            if isinstance(output_arg, int):
                output_metadata.indexes_with_symint.add(idx)
            output_metadata.indexes_with_no_grad.add(idx)
            continue

        # Check node metadata for type information
        if output_arg.meta.get("val") is None:
            # If we don't have complete metadata for all outputs, fall back to execution
            # This is important for correctness (e.g., detecting SymInts) even though it
            # runs side-effectful operations
            return _get_output_metadata_by_execution(subgraph, *operands)

        val = output_arg.meta["val"]
        if isinstance(val, torch.SymInt):
            output_metadata.indexes_with_symint.add(idx)
            output_metadata.indexes_with_no_grad.add(idx)
        elif isinstance(val, torch.Tensor):
            # Check if tensor requires grad from metadata
            if hasattr(val, "requires_grad") and not val.requires_grad:
                output_metadata.indexes_with_no_grad.add(idx)
        else:
            # Non-tensor, non-symint (shouldn't happen but be safe)
            output_metadata.indexes_with_no_grad.add(idx)

    return output_metadata