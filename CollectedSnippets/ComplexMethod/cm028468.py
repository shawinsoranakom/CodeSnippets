def translate_file(model,
                   params,
                   subtokenizer,
                   input_file,
                   output_file=None,
                   print_all_translations=True,
                   distribution_strategy=None):
  """Translate lines in file, and save to output file if specified.

  Args:
    model: A Keras model, used to generate the translations.
    params: A dictionary, containing the translation related parameters.
    subtokenizer: A subtokenizer object, used for encoding and decoding source
      and translated lines.
    input_file: A file containing lines to translate.
    output_file: A file that stores the generated translations.
    print_all_translations: A bool. If true, all translations are printed to
      stdout.
    distribution_strategy: A distribution strategy, used to perform inference
      directly with tf.function instead of Keras model.predict().

  Raises:
    ValueError: if output file is invalid.
  """
  batch_size = params["decode_batch_size"]

  # Read and sort inputs by length. Keep dictionary (original index-->new index
  # in sorted list) to write translations in the original order.
  sorted_inputs, sorted_keys = _get_sorted_inputs(input_file)
  total_samples = len(sorted_inputs)
  num_decode_batches = (total_samples - 1) // batch_size + 1

  def input_generator():
    """Yield encoded strings from sorted_inputs."""
    for i in range(num_decode_batches):
      lines = [
          sorted_inputs[j + i * batch_size]
          for j in range(batch_size)
          if j + i * batch_size < total_samples
      ]
      lines = [_encode_and_add_eos(l, subtokenizer) for l in lines]
      if distribution_strategy:
        for j in range(batch_size - len(lines)):
          lines.append([tokenizer.EOS_ID])
      batch = tf_keras.preprocessing.sequence.pad_sequences(
          lines,
          maxlen=params["decode_max_length"],
          dtype="int32",
          padding="post")
      logging.info("Decoding batch %d out of %d.", i, num_decode_batches)
      yield batch

  @tf.function
  def predict_step(inputs):
    """Decoding step function for TPU runs."""

    def _step_fn(inputs):
      """Per replica step function."""
      tag = inputs[0]
      val_inputs = inputs[1]
      val_outputs, _ = model([val_inputs], training=False)
      return tag, val_outputs

    return distribution_strategy.run(_step_fn, args=(inputs,))

  translations = []
  if distribution_strategy:
    num_replicas = distribution_strategy.num_replicas_in_sync
    local_batch_size = params["decode_batch_size"] // num_replicas
  for i, text in enumerate(input_generator()):
    if distribution_strategy:
      text = np.reshape(text, [num_replicas, local_batch_size, -1])
      # Add tag to the input of each replica with the reordering logic after
      # outputs, to ensure the output order matches the input order.
      text = tf.constant(text)

      @tf.function
      def text_as_per_replica():
        replica_context = tf.distribute.get_replica_context()
        replica_id = replica_context.replica_id_in_sync_group
        return replica_id, text[replica_id]  # pylint: disable=cell-var-from-loop

      text = distribution_strategy.run(text_as_per_replica)
      outputs = distribution_strategy.experimental_local_results(
          predict_step(text))
      val_outputs = [output for _, output in outputs]

      val_outputs = np.reshape(val_outputs, [params["decode_batch_size"], -1])
    else:
      val_outputs, _ = model.predict(text)

    length = len(val_outputs)
    for j in range(length):
      if j + i * batch_size < total_samples:
        translation = _trim_and_decode(val_outputs[j], subtokenizer)
        translations.append(translation)
        if print_all_translations:
          logging.info("Translating:\n\tInput: %s\n\tOutput: %s",
                       sorted_inputs[j + i * batch_size], translation)

  # Write translations in the order they appeared in the original file.
  if output_file is not None:
    if tf.io.gfile.isdir(output_file):
      raise ValueError("File output is a directory, will not save outputs to "
                       "file.")
    logging.info("Writing to file %s", output_file)
    with tf.io.gfile.GFile(output_file, "w") as f:
      for i in sorted_keys:
        f.write("%s\n" % translations[i])