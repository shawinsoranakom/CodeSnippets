def _recurse_in_model(tensor):
    """Walk the existing model recursively to copy a submodel."""
    if tensor.experimental_ref() in memoized_results:
      return memoized_results[tensor.experimental_ref()]
    if (tensor.experimental_ref() == inputs.experimental_ref()) or (
        isinstance(inputs, list) and tensor in inputs):
      if tensor.experimental_ref() not in model_inputs_dict:
        model_inputs_dict[tensor.experimental_ref()] = tf.keras.layers.Input(
            tensor=tensor)
      out = model_inputs_dict[tensor.experimental_ref()]
    else:
      cur_inputs = output_to_layer_input[tensor.experimental_ref()]
      cur_layer = output_to_layer[tensor.experimental_ref()]
      if isinstance(cur_inputs, list):
        out = cur_layer([_recurse_in_model(inp) for inp in cur_inputs])
      else:
        out = cur_layer(_recurse_in_model(cur_inputs))
    memoized_results[tensor.experimental_ref()] = out
    return out