def get_partition_cudagraph_metadata(
    partition_map: GraphPartitionMap,
    metadata: CudagraphMetadata,
) -> CudagraphMetadata:
    """
    Convert the cudagraph metadata at the graph level to the graph partition level,
    given the graph partition info (i.e., mapping from partition input/output index
    to graph input/output index).
    """

    partition_placeholders = []
    partition_static_input_idxs: OrderedSet[int] = OrderedSet()
    partition_mutated_input_idxs: OrderedSet[int] = OrderedSet()
    for partition_input_idx, graph_input_idx in enumerate(
        partition_map.input_index_mapping
    ):
        if graph_input_idx in metadata.static_input_idxs:
            partition_static_input_idxs.add(partition_input_idx)

        if graph_input_idx in metadata.mutated_input_idxs:
            partition_mutated_input_idxs.add(partition_input_idx)

        if graph_input_idx is not None:
            placeholder = metadata.placeholders[graph_input_idx]
        else:
            # create a dummy placeholder info since this partition input is not a graph input
            placeholder = PlaceholderInfo(
                name=f"partition_{partition_map.id}_placeholder_{partition_input_idx}",
                stack_trace=None,
                users=[],
                mutating_use_stack_trace=None,
            )
        partition_placeholders.append(placeholder)

    partition_stack_traces = []
    for graph_output_idx in partition_map.output_index_mapping:
        if graph_output_idx is not None:
            partition_stack_traces.append(metadata.stack_traces[graph_output_idx])
        else:
            partition_stack_traces.append(None)

    partition_constants = {
        name: metadata.constants[name] for name in partition_map.constant_names
    }

    return CudagraphMetadata(
        partition_placeholders,
        partition_static_input_idxs,
        partition_mutated_input_idxs,
        partition_stack_traces,
        partition_constants,
    )