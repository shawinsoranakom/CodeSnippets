def _build_backbone(
      self,
      backbone: tf_keras.Model,
      input_specs: Mapping[str, tf_keras.layers.InputSpec],
      state_specs: Optional[Mapping[str, tf_keras.layers.InputSpec]] = None,
  ) -> Tuple[Mapping[str, Any], Any, Any]:
    """Builds the backbone network and gets states and endpoints.

    Args:
      backbone: the model backbone.
      input_specs: the model input spec to use.
      state_specs: a dict of states such that, if any of the keys match for a
        layer, will overwrite the contents of the buffer(s).

    Returns:
      inputs: a dict of input specs.
      endpoints: a dict of model endpoints.
      states: a dict of model states.
    """
    state_specs = state_specs if state_specs is not None else {}

    states = {
        name: tf_keras.Input(shape=spec.shape[1:], dtype=spec.dtype, name=name)
        for name, spec in state_specs.items()
    }
    image = tf_keras.Input(shape=input_specs['image'].shape[1:], name='image')
    inputs = {**states, 'image': image}

    if backbone.use_external_states:
      before_states = states
      endpoints, states = backbone(inputs)
      after_states = states

      new_states = set(after_states) - set(before_states)
      if new_states:
        raise ValueError(
            'Expected input and output states to be the same. Got extra states '
            '{}, expected {}'.format(new_states, set(before_states)))

      mismatched_shapes = {}
      for name in after_states:
        before_shape = before_states[name].shape
        after_shape = after_states[name].shape
        if len(before_shape) != len(after_shape):
          mismatched_shapes[name] = (before_shape, after_shape)
          continue
        for before, after in zip(before_shape, after_shape):
          if before is not None and after is not None and before != after:
            mismatched_shapes[name] = (before_shape, after_shape)
            break
      if mismatched_shapes:
        raise ValueError(
            'Got mismatched input and output state shapes: {}'.format(
                mismatched_shapes))
    else:
      endpoints, states = backbone(inputs)
    return inputs, endpoints, states