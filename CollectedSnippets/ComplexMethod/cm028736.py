def write_glue_classification(task,
                              model,
                              input_file,
                              output_file,
                              predict_batch_size,
                              seq_length,
                              class_names,
                              label_type='int',
                              min_float_value=None,
                              max_float_value=None):
  """Makes classification predictions for glue and writes to output file.

  Args:
    task: `Task` instance.
    model: `keras.Model` instance.
    input_file: Input test data file path.
    output_file: Output test data file path.
    predict_batch_size: Batch size for prediction.
    seq_length: Input sequence length.
    class_names: List of string class names.
    label_type: String denoting label type ('int', 'float'), defaults to 'int'.
    min_float_value: If set, predictions will be min-clipped to this value (only
      for regression when `label_type` is set to 'float'). Defaults to `None`
      (no clipping).
    max_float_value: If set, predictions will be max-clipped to this value (only
      for regression when `label_type` is set to 'float'). Defaults to `None`
      (no clipping).
  """
  if label_type not in ('int', 'float'):
    raise ValueError('Unsupported `label_type`. Given: %s, expected `int` or '
                     '`float`.' % label_type)

  data_config = sentence_prediction_dataloader.SentencePredictionDataConfig(
      input_path=input_file,
      global_batch_size=predict_batch_size,
      is_training=False,
      seq_length=seq_length,
      label_type=label_type,
      drop_remainder=False,
      include_example_id=True)
  predictions = sentence_prediction.predict(task, data_config, model)

  if label_type == 'float':
    min_float_value = (-sys.float_info.max
                       if min_float_value is None else min_float_value)
    max_float_value = (
        sys.float_info.max if max_float_value is None else max_float_value)

    # Clip predictions to range [min_float_value, max_float_value].
    predictions = [
        min(max(prediction, min_float_value), max_float_value)
        for prediction in predictions
    ]

  with tf.io.gfile.GFile(output_file, 'w') as writer:
    writer.write('index\tprediction\n')
    for index, prediction in enumerate(predictions):
      if label_type == 'float':
        # Regression.
        writer.write('%d\t%.3f\n' % (index, prediction))
      else:
        # Classification.
        writer.write('%d\t%s\n' % (index, class_names[prediction]))