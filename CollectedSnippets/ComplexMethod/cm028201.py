def _assert_model_fn_for_train_eval(self, configs, mode,
                                      class_agnostic=False):
    model_config = configs['model']
    train_config = configs['train_config']
    with tf.Graph().as_default():
      if mode == 'train':
        features, labels = _make_initializable_iterator(
            inputs.create_train_input_fn(configs['train_config'],
                                         configs['train_input_config'],
                                         configs['model'])()).get_next()
        model_mode = tf_estimator.ModeKeys.TRAIN
        batch_size = train_config.batch_size
      elif mode == 'eval':
        features, labels = _make_initializable_iterator(
            inputs.create_eval_input_fn(configs['eval_config'],
                                        configs['eval_input_config'],
                                        configs['model'])()).get_next()
        model_mode = tf_estimator.ModeKeys.EVAL
        batch_size = 1
      elif mode == 'eval_on_train':
        features, labels = _make_initializable_iterator(
            inputs.create_eval_input_fn(configs['eval_config'],
                                        configs['train_input_config'],
                                        configs['model'])()).get_next()
        model_mode = tf_estimator.ModeKeys.EVAL
        batch_size = 1

      detection_model_fn = functools.partial(
          model_builder.build, model_config=model_config, is_training=True)

      hparams = model_hparams.create_hparams(
          hparams_overrides='load_pretrained=false')

      model_fn = model_lib.create_model_fn(detection_model_fn, configs, hparams)
      estimator_spec = model_fn(features, labels, model_mode)

      self.assertIsNotNone(estimator_spec.loss)
      self.assertIsNotNone(estimator_spec.predictions)
      if mode == 'eval' or mode == 'eval_on_train':
        if class_agnostic:
          self.assertNotIn('detection_classes', estimator_spec.predictions)
        else:
          detection_classes = estimator_spec.predictions['detection_classes']
          self.assertEqual(batch_size, detection_classes.shape.as_list()[0])
          self.assertEqual(tf.float32, detection_classes.dtype)
        detection_boxes = estimator_spec.predictions['detection_boxes']
        detection_scores = estimator_spec.predictions['detection_scores']
        num_detections = estimator_spec.predictions['num_detections']
        self.assertEqual(batch_size, detection_boxes.shape.as_list()[0])
        self.assertEqual(tf.float32, detection_boxes.dtype)
        self.assertEqual(batch_size, detection_scores.shape.as_list()[0])
        self.assertEqual(tf.float32, detection_scores.dtype)
        self.assertEqual(tf.float32, num_detections.dtype)
        if mode == 'eval':
          self.assertIn('Detections_Left_Groundtruth_Right/0',
                        estimator_spec.eval_metric_ops)
      if model_mode == tf_estimator.ModeKeys.TRAIN:
        self.assertIsNotNone(estimator_spec.train_op)
      return estimator_spec