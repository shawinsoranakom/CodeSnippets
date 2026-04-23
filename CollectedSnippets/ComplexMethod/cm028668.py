def export_saved_model(
    model: tf_keras.Model,
    input_shape: Tuple[int, int, int, int, int],
    export_path: str = '/tmp/movinet/',
    causal: bool = False,
    bundle_input_init_states_fn: bool = True,
    checkpoint_path: Optional[str] = None,
    assert_checkpoint_objects_matched: bool = True,
) -> None:
  """Exports a MoViNet model to a saved model.

  Args:
    model: the tf_keras.Model to export.
    input_shape: The 5D spatiotemporal input shape of size [batch_size,
      num_frames, image_height, image_width, num_channels]. Set the field or a
      shape position in the field to None for dynamic input.
    export_path: Export path to save the saved_model file.
    causal: Run the model in causal mode.
    bundle_input_init_states_fn: Add init_states as a function signature to the
      saved model. This is not necessary if the input shape is static (e.g., for
      TF Lite).
    checkpoint_path: Checkpoint path to load. Leave blank to keep the model's
      initialization.
    assert_checkpoint_objects_matched: Whether to check the checkpoint objects
      exactly match those of the model.
  """

  # Use dimensions of 1 except the channels to export faster,
  # since we only really need the last dimension to build and get the output
  # states. These dimensions can be set to `None` once the model is built.
  input_shape_concrete = [1 if s is None else s for s in input_shape]
  model.build(input_shape_concrete)

  # Compile model to generate some internal Keras variables.
  model.compile()

  if checkpoint_path:
    checkpoint = tf.train.Checkpoint(model=model)
    status = checkpoint.restore(checkpoint_path)
    if assert_checkpoint_objects_matched:
      status.assert_existing_objects_matched()

  if causal:
    # Call the model once to get the output states. Call again with `states`
    # input to ensure that the inputs with the `states` argument is built
    # with the full output state shapes.
    input_image = tf.ones(input_shape_concrete)
    _, states = model({
        **model.init_states(input_shape_concrete), 'image': input_image})
    _ = model({**states, 'image': input_image})

    # Create a function to explicitly set the names of the outputs
    def predict(inputs):
      outputs, states = model(inputs)
      return {**states, 'logits': outputs}

    specs = {
        name: tf.TensorSpec(spec.shape, name=name, dtype=spec.dtype)
        for name, spec in model.initial_state_specs(
            input_shape).items()
    }
    specs['image'] = tf.TensorSpec(
        input_shape, dtype=model.dtype, name='image')

    predict_fn = tf.function(predict, jit_compile=True)
    predict_fn = predict_fn.get_concrete_function(specs)

    init_states_fn = tf.function(model.init_states, jit_compile=True)
    init_states_fn = init_states_fn.get_concrete_function(
        tf.TensorSpec([5], dtype=tf.int32))

    if bundle_input_init_states_fn:
      signatures = {'call': predict_fn, 'init_states': init_states_fn}
    else:
      signatures = predict_fn

    tf_keras.models.save_model(
        model, export_path, signatures=signatures)
  else:
    _ = model(tf.ones(input_shape_concrete))
    tf_keras.models.save_model(model, export_path)