def _inplace_buffer_and_input_mutations(
    graph: torch.fx.Graph,
    graph_signature: ExportGraphSignature,
) -> None:
    """Transform buffer and input mutations from their functionalized form
    into copy_ nodes in the graph.

    Functionalization represents a buffer mutation by passing the buffer as
    an input and output. For example, consider the eager code:
        def forward(self, x):
            self.buffer += x
            return x * x

    This corresponds to a graph that looks like:
        def forward(self, buffer, x):
            mutated_buffer = aten.add(buffer, x)
            mul = aten.mul(x, x)
            return (mutated_buffer, mul)

    We want to inplace this into something that looks like the original
    eager code:
        def forward(self, buffer, x):
            mutated_buffer = aten.add(buffer, x)
            buffer.copy_(mutated_buffer)
            mul = aten.mul(x, x)
            return (mul,)

    Input mutations are handled similarly.
    """
    output_node = next(iter(reversed(graph.nodes)))
    if output_node.op != "output" or len(output_node.args) != 1:
        raise AssertionError(
            f"expected output node with op='output' and 1 arg, got op={output_node.op!r} with {len(output_node.args)} args"
        )
    return_args = output_node.args[0]

    input_name_to_node = {
        node.name: node for node in graph.nodes if node.op == "placeholder"
    }
    mutation_name_to_input_name = {}

    # Collect mutated buffers.
    buffer_fqn_to_input_name = {
        buffer_fqn: k for k, buffer_fqn in graph_signature.inputs_to_buffers.items()
    }
    mutation_name_to_input_name = {
        k: buffer_fqn_to_input_name[buffer_fqn]
        for k, buffer_fqn in graph_signature.buffers_to_mutate.items()
    }
    # Collect mutated user inputs.
    mutation_name_to_input_name.update(graph_signature.user_inputs_to_mutate)

    num_mutations = len(mutation_name_to_input_name)

    for mutation in return_args[:num_mutations]:
        input_name = mutation_name_to_input_name[mutation.name]
        input_node = input_name_to_node[input_name]

        with graph.inserting_after(mutation):
            # Create a copy_ node that inplaces the mutation.
            new_node = graph.create_node(
                "call_function", torch.ops.aten.copy_.default, (input_node, mutation)
            )
            for k, v in mutation.meta.items():
                new_node.meta[k] = v
        # Replace all uses of the previously functional mutation with
        # our copy_ node.
        mutation.replace_all_uses_with(new_node, lambda x: x is not new_node)

    # Remove the mutated buffer / input from the graph outputs, since we don't
    # need to thread it through anymore.
    user_outputs = tuple(return_args[num_mutations:])
    output_node.args = ((user_outputs),)