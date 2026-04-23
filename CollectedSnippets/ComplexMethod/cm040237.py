def clone_graph_nodes(inputs, outputs):
    """Clone the `Node` between the inputs and output tensors.

    This function is used to create a new functional model from any intermediate
    Keras tensors. The clone of the nodes mimic the behavior of reconstructing
    the functional graph network by re-executing all the `__call__()` methods.
    The cloned nodes will be appended to the layers.

    Note that a new `keras.Input` will be created for any items in the
    `inputs`

    Args:
    inputs: A nested structure of `KerasTensor` instances.
    outputs: A nested structure of `KerasTensor` instances.

    Returns:
        A pair of inputs and outputs, with cloned `KerasTensor` instances.
        They can be used to create a new functional model.
    """
    nodes_to_clone = find_nodes_by_inputs_and_outputs(inputs, outputs)
    cloned_inputs = []
    cloned_outputs = []
    # We not only need to create copies of Nodes (mimic the calls), also need to
    # clone Keras tensors to avoid the override of _keras_history attached on
    # the Keras tensor. The following dict is used to track any keras tensor we
    # cloned The key is the string ID of the original keras tensor, and value is
    # the cloned Keras tensor instance.
    kt_id_mapping = {}
    op_id_mapping = {}

    for kt_input in tree.flatten(inputs):
        if is_input_keras_tensor(kt_input):
            # For any existing Keras tensor from keras.Input, leave them as is.
            cloned_inputs.append(kt_input)
            kt_id_mapping[id(kt_input)] = kt_input
        else:
            # We need to create a new Keras tensor for any intermediate tensor
            original_op = kt_input._keras_history.operation
            optional = False
            if isinstance(original_op, InputLayer):
                optional = original_op.optional
            cloned_input = Input(
                batch_shape=kt_input.shape,
                dtype=kt_input.dtype,
                sparse=kt_input.sparse,
                name=f"{kt_input.name}CLONE",
                optional=optional,
            )
            cloned_inputs.append(cloned_input)
            kt_id_mapping[id(kt_input)] = cloned_input
            op_id_mapping[id(kt_input._keras_history[0])] = (
                cloned_input._keras_history[0]
            )
    cloned_inputs = tree.pack_sequence_as(inputs, cloned_inputs)

    for kt_output in tree.flatten(outputs):
        cpy = clone_single_keras_tensor(kt_output)
        # We reuse the _keras_history here, which contains the old information.
        cpy._keras_history = kt_output._keras_history
        cloned_outputs.append(cpy)
        kt_id_mapping[id(kt_output)] = cpy
    cloned_outputs = tree.pack_sequence_as(outputs, cloned_outputs)

    for node in nodes_to_clone:
        if id(node.operation) in op_id_mapping:
            operation = op_id_mapping[id(node.operation)]
        else:
            operation = node.operation
        # Clone any Keras tensor to avoid override of _keras_history
        # Or reuse an existing Keras tensor if it has already been cloned.
        output_copy = clone_keras_tensors(node.output_tensors, kt_id_mapping)
        if not isinstance(operation, InputLayer):
            call_args_copy = clone_keras_tensors(
                node.arguments.args, kt_id_mapping
            )
            call_kwargs_copy = clone_keras_tensors(
                node.arguments.kwargs, kt_id_mapping
            )
        else:
            call_args_copy = ()
            call_kwargs_copy = {}
        # Creating new nodes based on the existing node information.  Node wires
        # itself to inbound and outbound layers.  The Node constructor actually
        # updates this layer's self._inbound_nodes, sets _keras_history on the
        # outputs, and adds itself to the `_outbound_nodes` of the layers that
        # produced the inputs to this layer call.
        Node(
            operation,
            call_args=call_args_copy,
            call_kwargs=call_kwargs_copy,
            outputs=output_copy,
        )
    return cloned_inputs, cloned_outputs