def parse_side_inputs(side_input_shapes_string, side_input_names_string,
                      side_input_types_string):
  """Parses side input flags.

  Args:
    side_input_shapes_string: The shape of the side input tensors, provided as a
      comma-separated list of integers. A value of -1 is used for unknown
      dimensions. A `/` denotes a break, starting the shape of the next side
      input tensor.
    side_input_names_string: The names of the side input tensors, provided as a
      comma-separated list of strings.
    side_input_types_string: The type of the side input tensors, provided as a
      comma-separated list of types, each of `string`, `integer`, or `float`.

  Returns:
    side_input_shapes: A list of shapes.
    side_input_names: A list of strings.
    side_input_types: A list of tensorflow dtypes.

  """
  if side_input_shapes_string:
    side_input_shapes = []
    for side_input_shape_list in side_input_shapes_string.split('/'):
      side_input_shape = [
          int(dim) if dim != '-1' else None
          for dim in side_input_shape_list.split(',')
      ]
      side_input_shapes.append(side_input_shape)
  else:
    raise ValueError('When using side_inputs, side_input_shapes must be '
                     'specified in the input flags.')
  if side_input_names_string:
    side_input_names = list(side_input_names_string.split(','))
  else:
    raise ValueError('When using side_inputs, side_input_names must be '
                     'specified in the input flags.')
  if side_input_types_string:
    typelookup = {'float': tf.float32, 'int': tf.int32, 'string': tf.string}
    side_input_types = [
        typelookup[side_input_type]
        for side_input_type in side_input_types_string.split(',')
    ]
  else:
    raise ValueError('When using side_inputs, side_input_types must be '
                     'specified in the input flags.')
  return side_input_shapes, side_input_names, side_input_types