def multi_input_rnn_decoder(decoder_inputs,
                            initial_state,
                            cell,
                            sequence_step,
                            selection_strategy='RANDOM',
                            is_training=None,
                            is_quantized=False,
                            preprocess_fn_list=None,
                            pre_bottleneck=False,
                            flatten_state=False,
                            scope=None):
  """RNN decoder for the Interleaved LSTM-SSD model.

  This decoder takes multiple sequences of inputs and selects the input to feed
  to the rnn at each timestep using its selection_strategy, which can be random,
  learned, or deterministic.
  This decoder returns a list of all states, rather than only the final state.
  Args:
    decoder_inputs: A list of lists of 2D Tensors [batch_size x input_size].
    initial_state: 2D Tensor with shape [batch_size x cell.state_size].
    cell: rnn_cell.RNNCell defining the cell function and size.
    sequence_step: Tensor [batch_size] of the step number of the first elements
      in the sequence.
    selection_strategy: Method for picking the decoder_input to use at each
      timestep. Must be 'RANDOM', 'SKIPX' for integer X,  where X is the number
      of times to use the second input before using the first.
    is_training: boolean, whether the network is training. When using learned
      selection, attempts exploration if training.
    is_quantized: flag to enable/disable quantization mode.
    preprocess_fn_list: List of functions accepting two tensor arguments: one
      timestep of decoder_inputs and the lstm state. If not None,
      decoder_inputs[i] will be updated with preprocess_fn[i] at the start of
      each timestep.
    pre_bottleneck: if True, use separate bottleneck weights for each sequence.
      Useful when input sequences have differing numbers of channels. Final
      bottlenecks will have the same dimension.
    flatten_state: Whether the LSTM state is flattened.
    scope: optional VariableScope for the created subgraph.
  Returns:
    A tuple of the form (outputs, state), where:
      outputs: A list of the same length as decoder_inputs of 2D Tensors with
        shape [batch_size x output_size] containing generated outputs.
      states: A list of the same length as decoder_inputs of the state of each
        cell at each time-step. It is a 2D Tensor of shape
        [batch_size x cell.state_size].
  Raises:
    ValueError: If selection_strategy is not recognized or unexpected unroll
      length.
  """
  if flatten_state and len(decoder_inputs[0]) > 1:
    raise ValueError('In export mode, unroll length should not be more than 1')
  with tf.variable_scope(scope) if scope else _NoVariableScope():
    state_tuple = initial_state
    outputs = []
    states = []
    batch_size = decoder_inputs[0][0].shape[0].value
    num_sequences = len(decoder_inputs)
    sequence_length = len(decoder_inputs[0])

    for local_step in range(sequence_length):
      for sequence_index in range(num_sequences):
        if preprocess_fn_list is not None:
          decoder_inputs[sequence_index][local_step] = (
              preprocess_fn_list[sequence_index](
                  decoder_inputs[sequence_index][local_step], state_tuple[0]))
        if pre_bottleneck:
          decoder_inputs[sequence_index][local_step] = cell.pre_bottleneck(
              inputs=decoder_inputs[sequence_index][local_step],
              state=state_tuple[1],
              input_index=sequence_index)

      action = generate_action(selection_strategy, local_step, sequence_step,
                               [batch_size, 1, 1, 1])
      inputs, _ = (
          select_inputs(decoder_inputs, action, local_step, is_training,
                        is_quantized))
      # Mark base network endpoints under raw_inputs/
      with tf.name_scope(None):
        inputs = tf.identity(inputs, 'raw_inputs/base_endpoint')
      output, state_tuple_out = cell(inputs, state_tuple)
      state_tuple = select_state(state_tuple, state_tuple_out, action)

      outputs.append(output)
      states.append(state_tuple)
  return outputs, states