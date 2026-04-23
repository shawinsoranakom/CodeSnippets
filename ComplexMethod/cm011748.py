def clean_removed_buffer_from_partition_signatures(
        self, signature: GraphPartitionSignature
    ) -> GraphPartitionSignature:
        """
        Updates the partition signature by removing buffers specified in
        V.graph.removed_buffers. See [Note: Removed Graph Partition Arguments]
        """
        input_nodes = {
            name: buffer
            for name, buffer in signature.input_nodes.items()
            if name not in V.graph.removed_buffers
        }
        input_deallocation = {
            name: val
            for name, val in signature.input_deallocation.items()
            if name not in V.graph.removed_buffers
        }
        output_nodes = [
            node
            for node in signature.output_nodes
            if node.maybe_get_name() not in V.graph.removed_buffers
        ]
        constant_names = [
            name
            for name in signature.constant_names
            if name not in V.graph.removed_buffers
        ]
        return GraphPartitionSignature(
            signature.symbol_inputs,
            input_nodes,
            output_nodes,
            input_deallocation,
            signature.skip_cudagraph,
            constant_names,
        )