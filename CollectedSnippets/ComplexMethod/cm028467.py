def custom_main(custom_callbacks=None, custom_metrics=None):
  """Run classification or regression.

  Args:
    custom_callbacks: list of tf_keras.Callbacks passed to training loop.
    custom_metrics: list of metrics passed to the training loop.
  """
  gin.parse_config_files_and_bindings(FLAGS.gin_file, FLAGS.gin_param)

  with tf.io.gfile.GFile(FLAGS.input_meta_data_path, 'rb') as reader:
    input_meta_data = json.loads(reader.read().decode('utf-8'))
  label_type = LABEL_TYPES_MAP[input_meta_data.get('label_type', 'int')]
  include_sample_weights = input_meta_data.get('has_sample_weights', False)

  if not FLAGS.model_dir:
    FLAGS.model_dir = '/tmp/bert20/'

  bert_config = bert_configs.BertConfig.from_json_file(FLAGS.bert_config_file)

  if FLAGS.mode == 'export_only':
    export_classifier(FLAGS.model_export_path, input_meta_data, bert_config,
                      FLAGS.model_dir)
    return

  strategy = distribute_utils.get_distribution_strategy(
      distribution_strategy=FLAGS.distribution_strategy,
      num_gpus=FLAGS.num_gpus,
      tpu_address=FLAGS.tpu)
  eval_input_fn = get_dataset_fn(
      FLAGS.eval_data_path,
      input_meta_data['max_seq_length'],
      FLAGS.eval_batch_size,
      is_training=False,
      label_type=label_type,
      include_sample_weights=include_sample_weights)

  if FLAGS.mode == 'predict':
    num_labels = input_meta_data.get('num_labels', 1)
    with strategy.scope():
      classifier_model = bert_models.classifier_model(
          bert_config, num_labels)[0]
      checkpoint = tf.train.Checkpoint(model=classifier_model)
      latest_checkpoint_file = (
          FLAGS.predict_checkpoint_path or
          tf.train.latest_checkpoint(FLAGS.model_dir))
      assert latest_checkpoint_file
      logging.info('Checkpoint file %s found and restoring from '
                   'checkpoint', latest_checkpoint_file)
      checkpoint.restore(
          latest_checkpoint_file).assert_existing_objects_matched()
      preds, _ = get_predictions_and_labels(
          strategy,
          classifier_model,
          eval_input_fn,
          is_regression=(num_labels == 1),
          return_probs=True)
    output_predict_file = os.path.join(FLAGS.model_dir, 'test_results.tsv')
    with tf.io.gfile.GFile(output_predict_file, 'w') as writer:
      logging.info('***** Predict results *****')
      for probabilities in preds:
        output_line = '\t'.join(
            str(class_probability)
            for class_probability in probabilities) + '\n'
        writer.write(output_line)
    return

  if FLAGS.mode != 'train_and_eval':
    raise ValueError('Unsupported mode is specified: %s' % FLAGS.mode)
  train_input_fn = get_dataset_fn(
      FLAGS.train_data_path,
      input_meta_data['max_seq_length'],
      FLAGS.train_batch_size,
      is_training=True,
      label_type=label_type,
      include_sample_weights=include_sample_weights,
      num_samples=FLAGS.train_data_size)
  run_bert(
      strategy,
      input_meta_data,
      bert_config,
      train_input_fn,
      eval_input_fn,
      custom_callbacks=custom_callbacks,
      custom_metrics=custom_metrics)