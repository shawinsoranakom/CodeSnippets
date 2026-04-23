def codegen_partition_call(
        self,
        partition_id: int,
        partition_signatures: ir.GraphPartitionSignature,
    ):
        """Generate code to call a graph partition"""
        input_deallocation = partition_signatures.input_deallocation
        output_nodes = partition_signatures.output_nodes

        input_names = list(input_deallocation.keys()) + [
            symbol_input.name for symbol_input in partition_signatures.symbol_inputs
        ]

        inputs = ", ".join(input_names) + ("," if len(input_names) == 1 else "")

        output_names = [node.get_name() for node in output_nodes]
        outputs = ", ".join(output_names) + ("," if len(output_nodes) == 1 else "")

        # Create a list of inputs for the subgraph call
        self.writeline(f"partition{partition_id}_args = [{inputs}]")

        names_to_del = [
            name for name, deallocate in input_deallocation.items() if deallocate
        ]
        if names_to_del:
            self.writeline(f"del {', '.join(names_to_del)}")

        # Call the subgraph launcher function
        self.writeline(
            f"({outputs}) = self.partitions[{partition_id}](partition{partition_id}_args)"
        )
        self.writeline(f"del partition{partition_id}_args")