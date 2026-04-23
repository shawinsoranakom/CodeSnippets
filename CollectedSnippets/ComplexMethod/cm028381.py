def main(unused_argv):
  tf.logging.set_verbosity(tf.logging.INFO)

  dataset = data_generator.Dataset(
      dataset_name=FLAGS.dataset,
      split_name=FLAGS.eval_split,
      dataset_dir=FLAGS.dataset_dir,
      batch_size=FLAGS.eval_batch_size,
      crop_size=[int(sz) for sz in FLAGS.eval_crop_size],
      min_resize_value=FLAGS.min_resize_value,
      max_resize_value=FLAGS.max_resize_value,
      resize_factor=FLAGS.resize_factor,
      model_variant=FLAGS.model_variant,
      num_readers=2,
      is_training=False,
      should_shuffle=False,
      should_repeat=False)

  tf.gfile.MakeDirs(FLAGS.eval_logdir)
  tf.logging.info('Evaluating on %s set', FLAGS.eval_split)

  with tf.Graph().as_default():
    samples = dataset.get_one_shot_iterator().get_next()

    model_options = common.ModelOptions(
        outputs_to_num_classes={common.OUTPUT_TYPE: dataset.num_of_classes},
        crop_size=[int(sz) for sz in FLAGS.eval_crop_size],
        atrous_rates=FLAGS.atrous_rates,
        output_stride=FLAGS.output_stride)

    # Set shape in order for tf.contrib.tfprof.model_analyzer to work properly.
    samples[common.IMAGE].set_shape(
        [FLAGS.eval_batch_size,
         int(FLAGS.eval_crop_size[0]),
         int(FLAGS.eval_crop_size[1]),
         3])
    if tuple(FLAGS.eval_scales) == (1.0,):
      tf.logging.info('Performing single-scale test.')
      predictions = model.predict_labels(samples[common.IMAGE], model_options,
                                         image_pyramid=FLAGS.image_pyramid)
    else:
      tf.logging.info('Performing multi-scale test.')
      if FLAGS.quantize_delay_step >= 0:
        raise ValueError(
            'Quantize mode is not supported with multi-scale test.')

      predictions = model.predict_labels_multi_scale(
          samples[common.IMAGE],
          model_options=model_options,
          eval_scales=FLAGS.eval_scales,
          add_flipped_images=FLAGS.add_flipped_images)
    predictions = predictions[common.OUTPUT_TYPE]
    predictions = tf.reshape(predictions, shape=[-1])
    labels = tf.reshape(samples[common.LABEL], shape=[-1])
    weights = tf.to_float(tf.not_equal(labels, dataset.ignore_label))

    # Set ignore_label regions to label 0, because metrics.mean_iou requires
    # range of labels = [0, dataset.num_classes). Note the ignore_label regions
    # are not evaluated since the corresponding regions contain weights = 0.
    labels = tf.where(
        tf.equal(labels, dataset.ignore_label), tf.zeros_like(labels), labels)

    predictions_tag = 'miou'
    for eval_scale in FLAGS.eval_scales:
      predictions_tag += '_' + str(eval_scale)
    if FLAGS.add_flipped_images:
      predictions_tag += '_flipped'

    # Define the evaluation metric.
    metric_map = {}
    num_classes = dataset.num_of_classes
    metric_map['eval/%s_overall' % predictions_tag] = tf.metrics.mean_iou(
        labels=labels, predictions=predictions, num_classes=num_classes,
        weights=weights)
    # IoU for each class.
    one_hot_predictions = tf.one_hot(predictions, num_classes)
    one_hot_predictions = tf.reshape(one_hot_predictions, [-1, num_classes])
    one_hot_labels = tf.one_hot(labels, num_classes)
    one_hot_labels = tf.reshape(one_hot_labels, [-1, num_classes])
    for c in range(num_classes):
      predictions_tag_c = '%s_class_%d' % (predictions_tag, c)
      tp, tp_op = tf.metrics.true_positives(
          labels=one_hot_labels[:, c], predictions=one_hot_predictions[:, c],
          weights=weights)
      fp, fp_op = tf.metrics.false_positives(
          labels=one_hot_labels[:, c], predictions=one_hot_predictions[:, c],
          weights=weights)
      fn, fn_op = tf.metrics.false_negatives(
          labels=one_hot_labels[:, c], predictions=one_hot_predictions[:, c],
          weights=weights)
      tp_fp_fn_op = tf.group(tp_op, fp_op, fn_op)
      iou = tf.where(tf.greater(tp + fn, 0.0),
                     tp / (tp + fn + fp),
                     tf.constant(np.NaN))
      metric_map['eval/%s' % predictions_tag_c] = (iou, tp_fp_fn_op)

    (metrics_to_values,
     metrics_to_updates) = contrib_metrics.aggregate_metric_map(metric_map)

    summary_ops = []
    for metric_name, metric_value in six.iteritems(metrics_to_values):
      op = tf.summary.scalar(metric_name, metric_value)
      op = tf.Print(op, [metric_value], metric_name)
      summary_ops.append(op)

    summary_op = tf.summary.merge(summary_ops)
    summary_hook = contrib_training.SummaryAtEndHook(
        log_dir=FLAGS.eval_logdir, summary_op=summary_op)
    hooks = [summary_hook]

    num_eval_iters = None
    if FLAGS.max_number_of_evaluations > 0:
      num_eval_iters = FLAGS.max_number_of_evaluations

    if FLAGS.quantize_delay_step >= 0:
      contrib_quantize.create_eval_graph()

    contrib_tfprof.model_analyzer.print_model_analysis(
        tf.get_default_graph(),
        tfprof_options=contrib_tfprof.model_analyzer
        .TRAINABLE_VARS_PARAMS_STAT_OPTIONS)
    contrib_tfprof.model_analyzer.print_model_analysis(
        tf.get_default_graph(),
        tfprof_options=contrib_tfprof.model_analyzer.FLOAT_OPS_OPTIONS)
    contrib_training.evaluate_repeatedly(
        checkpoint_dir=FLAGS.checkpoint_dir,
        master=FLAGS.master,
        eval_ops=list(metrics_to_updates.values()),
        max_number_of_evaluations=num_eval_iters,
        hooks=hooks,
        eval_interval_secs=FLAGS.eval_interval_secs)