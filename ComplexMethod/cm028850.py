def convert_to_feature(value, value_type=None):
  """Converts the given python object to a tf.train.Feature.

  Args:
    value: int, float, bytes or a list of them.
    value_type: optional, if specified, forces the feature to be of the given
      type. Otherwise, type is inferred automatically. Can be one of
      ['bytes', 'int64', 'float', 'bytes_list', 'int64_list', 'float_list']

  Returns:
    feature: A tf.train.Feature object.
  """

  if value_type is None:

    element = value[0] if isinstance(value, list) else value

    if isinstance(element, bytes):
      value_type = 'bytes'

    elif isinstance(element, (int, np.integer)):
      value_type = 'int64'

    elif isinstance(element, (float, np.floating)):
      value_type = 'float'

    else:
      raise ValueError('Cannot convert type {} to feature'.
                       format(type(element)))

    if isinstance(value, list):
      value_type = value_type + '_list'

  if value_type == 'int64':
    return tf.train.Feature(int64_list=tf.train.Int64List(value=[value]))

  elif value_type == 'int64_list':
    value = np.asarray(value).astype(np.int64).reshape(-1)
    return tf.train.Feature(int64_list=tf.train.Int64List(value=value))

  elif value_type == 'float':
    return tf.train.Feature(float_list=tf.train.FloatList(value=[value]))

  elif value_type == 'float_list':
    value = np.asarray(value).astype(np.float32).reshape(-1)
    return tf.train.Feature(float_list=tf.train.FloatList(value=value))

  elif value_type == 'bytes':
    return tf.train.Feature(bytes_list=tf.train.BytesList(value=[value]))

  elif value_type == 'bytes_list':
    return tf.train.Feature(bytes_list=tf.train.BytesList(value=value))

  else:
    raise ValueError('Unknown value_type parameter - {}'.format(value_type))