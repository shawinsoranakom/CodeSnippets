def finalize_serving(model_output, export_config):
  """Adds extra layers based on the provided configuration."""

  if isinstance(model_output, dict):
    return {
        key: finalize_serving(model_output[key], export_config)
        for key in model_output
    }

  finalize_method = export_config.finalize_method
  output_layer = model_output
  if not finalize_method or finalize_method[0] == 'none':
    return output_layer
  discrete = False
  for i in range(len(finalize_method)):
    if finalize_method[i] == 'argmax':
      discrete = True
      is_argmax_last = (i + 1) == len(finalize_method)
      if is_argmax_last:
        output_layer = tf.argmax(
            output_layer, axis=3, output_type=tf.dtypes.int32)
      else:
        # TODO(tohaspiridonov): add first_match=False when cl/383951533 submited
        output_layer = custom_layers.argmax(
            output_layer, keepdims=True, epsilon=1e-3)
    elif finalize_method[i] == 'squeeze':
      output_layer = tf.squeeze(output_layer, axis=3)
    else:
      resize_params = finalize_method[i].split('resize')
      if len(resize_params) != 2 or resize_params[0]:
        raise ValueError('Cannot finalize with ' + finalize_method[i] + '.')
      resize_to_size = int(resize_params[1])
      if discrete:
        output_layer = tf.image.resize(
            output_layer, [resize_to_size, resize_to_size],
            method=tf.image.ResizeMethod.NEAREST_NEIGHBOR)
      else:
        output_layer = tf.image.resize(
            output_layer, [resize_to_size, resize_to_size],
            method=tf.image.ResizeMethod.BILINEAR)
  return output_layer