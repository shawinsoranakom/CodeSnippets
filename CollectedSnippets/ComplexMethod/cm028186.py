def build_detection_graph(input_type, detection_model, input_shape,
                          output_collection_name, graph_hook_fn,
                          use_side_inputs=False, side_input_shapes=None,
                          side_input_names=None, side_input_types=None):
  """Build the detection graph."""
  if input_type not in input_placeholder_fn_map:
    raise ValueError('Unknown input type: {}'.format(input_type))
  placeholder_args = {}
  side_inputs = {}
  if input_shape is not None:
    if (input_type != 'image_tensor' and
        input_type != 'encoded_image_string_tensor' and
        input_type != 'tf_example' and
        input_type != 'tf_sequence_example'):
      raise ValueError('Can only specify input shape for `image_tensor`, '
                       '`encoded_image_string_tensor`, `tf_example`, '
                       ' or `tf_sequence_example` inputs.')
    placeholder_args['input_shape'] = input_shape
  placeholder_tensor, input_tensors = input_placeholder_fn_map[input_type](
      **placeholder_args)
  placeholder_tensors = {'inputs': placeholder_tensor}
  if use_side_inputs:
    for idx, side_input_name in enumerate(side_input_names):
      side_input_placeholder, side_input = _side_input_tensor_placeholder(
          side_input_shapes[idx], side_input_name, side_input_types[idx])
      print(side_input)
      side_inputs[side_input_name] = side_input
      placeholder_tensors[side_input_name] = side_input_placeholder
  outputs = _get_outputs_from_inputs(
      input_tensors=input_tensors,
      detection_model=detection_model,
      output_collection_name=output_collection_name,
      **side_inputs)

  # Add global step to the graph.
  slim.get_or_create_global_step()

  if graph_hook_fn: graph_hook_fn()

  return outputs, placeholder_tensors