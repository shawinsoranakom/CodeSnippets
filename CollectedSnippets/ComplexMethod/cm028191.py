def model_fn(features, labels, mode, params=None):
    """Constructs the object detection model.

    Args:
      features: Dictionary of feature tensors, returned from `input_fn`.
      labels: Dictionary of groundtruth tensors if mode is TRAIN or EVAL,
        otherwise None.
      mode: Mode key from tf.estimator.ModeKeys.
      params: Parameter dictionary passed from the estimator.

    Returns:
      An `EstimatorSpec` that encapsulates the model and its serving
        configurations.
    """
    params = params or {}
    total_loss, train_op, detections, export_outputs = None, None, None, None
    is_training = mode == tf_estimator.ModeKeys.TRAIN

    # Make sure to set the Keras learning phase. True during training,
    # False for inference.
    tf.keras.backend.set_learning_phase(is_training)
    # Set policy for mixed-precision training with Keras-based models.
    if use_tpu and train_config.use_bfloat16:
      # Enable v2 behavior, as `mixed_bfloat16` is only supported in TF 2.0.
      tf.keras.layers.enable_v2_dtype_behavior()
      tf2.keras.mixed_precision.set_global_policy('mixed_bfloat16')
    detection_model = detection_model_fn(
        is_training=is_training, add_summaries=(not use_tpu))
    scaffold_fn = None

    if mode == tf_estimator.ModeKeys.TRAIN:
      labels = unstack_batch(
          labels,
          unpad_groundtruth_tensors=train_config.unpad_groundtruth_tensors)
    elif mode == tf_estimator.ModeKeys.EVAL:
      # For evaling on train data, it is necessary to check whether groundtruth
      # must be unpadded.
      boxes_shape = (
          labels[
              fields.InputDataFields.groundtruth_boxes].get_shape().as_list())
      unpad_groundtruth_tensors = boxes_shape[1] is not None and not use_tpu
      labels = unstack_batch(
          labels, unpad_groundtruth_tensors=unpad_groundtruth_tensors)

    if mode in (tf_estimator.ModeKeys.TRAIN, tf_estimator.ModeKeys.EVAL):
      provide_groundtruth(detection_model, labels)

    preprocessed_images = features[fields.InputDataFields.image]

    side_inputs = detection_model.get_side_inputs(features)

    if use_tpu and train_config.use_bfloat16:
      with tf.tpu.bfloat16_scope():
        prediction_dict = detection_model.predict(
            preprocessed_images,
            features[fields.InputDataFields.true_image_shape], **side_inputs)
        prediction_dict = ops.bfloat16_to_float32_nested(prediction_dict)
    else:
      prediction_dict = detection_model.predict(
          preprocessed_images,
          features[fields.InputDataFields.true_image_shape], **side_inputs)

    def postprocess_wrapper(args):
      return detection_model.postprocess(args[0], args[1])

    if mode in (tf_estimator.ModeKeys.EVAL, tf_estimator.ModeKeys.PREDICT):
      if use_tpu and postprocess_on_cpu:
        detections = tf.tpu.outside_compilation(
            postprocess_wrapper,
            (prediction_dict,
             features[fields.InputDataFields.true_image_shape]))
      else:
        detections = postprocess_wrapper(
            (prediction_dict,
             features[fields.InputDataFields.true_image_shape]))

    if mode == tf_estimator.ModeKeys.TRAIN:
      load_pretrained = hparams.load_pretrained if hparams else False
      if train_config.fine_tune_checkpoint and load_pretrained:
        if not train_config.fine_tune_checkpoint_type:
          # train_config.from_detection_checkpoint field is deprecated. For
          # backward compatibility, set train_config.fine_tune_checkpoint_type
          # based on train_config.from_detection_checkpoint.
          if train_config.from_detection_checkpoint:
            train_config.fine_tune_checkpoint_type = 'detection'
          else:
            train_config.fine_tune_checkpoint_type = 'classification'
        asg_map = detection_model.restore_map(
            fine_tune_checkpoint_type=train_config.fine_tune_checkpoint_type,
            load_all_detection_checkpoint_vars=(
                train_config.load_all_detection_checkpoint_vars))
        available_var_map = (
            variables_helper.get_variables_available_in_checkpoint(
                asg_map,
                train_config.fine_tune_checkpoint,
                include_global_step=False))
        if use_tpu:

          def tpu_scaffold():
            tf.train.init_from_checkpoint(train_config.fine_tune_checkpoint,
                                          available_var_map)
            return tf.train.Scaffold()

          scaffold_fn = tpu_scaffold
        else:
          tf.train.init_from_checkpoint(train_config.fine_tune_checkpoint,
                                        available_var_map)

    if mode in (tf_estimator.ModeKeys.TRAIN, tf_estimator.ModeKeys.EVAL):
      if (mode == tf_estimator.ModeKeys.EVAL and
          eval_config.use_dummy_loss_in_eval):
        total_loss = tf.constant(1.0)
        losses_dict = {'Loss/total_loss': total_loss}
      else:
        losses_dict = detection_model.loss(
            prediction_dict, features[fields.InputDataFields.true_image_shape])
        losses = [loss_tensor for loss_tensor in losses_dict.values()]
        if train_config.add_regularization_loss:
          regularization_losses = detection_model.regularization_losses()
          if use_tpu and train_config.use_bfloat16:
            regularization_losses = ops.bfloat16_to_float32_nested(
                regularization_losses)
          if regularization_losses:
            regularization_loss = tf.add_n(
                regularization_losses, name='regularization_loss')
            losses.append(regularization_loss)
            losses_dict['Loss/regularization_loss'] = regularization_loss
        total_loss = tf.add_n(losses, name='total_loss')
        losses_dict['Loss/total_loss'] = total_loss

      if 'graph_rewriter_config' in configs:
        graph_rewriter_fn = graph_rewriter_builder.build(
            configs['graph_rewriter_config'], is_training=is_training)
        graph_rewriter_fn()

      # TODO(rathodv): Stop creating optimizer summary vars in EVAL mode once we
      # can write learning rate summaries on TPU without host calls.
      global_step = tf.train.get_or_create_global_step()
      training_optimizer, optimizer_summary_vars = optimizer_builder.build(
          train_config.optimizer)

    if mode == tf_estimator.ModeKeys.TRAIN:
      if use_tpu:
        training_optimizer = tf.tpu.CrossShardOptimizer(training_optimizer)

      # Optionally freeze some layers by setting their gradients to be zero.
      trainable_variables = None
      include_variables = (
          train_config.update_trainable_variables
          if train_config.update_trainable_variables else None)
      exclude_variables = (
          train_config.freeze_variables
          if train_config.freeze_variables else None)
      trainable_variables = slim.filter_variables(
          tf.trainable_variables(),
          include_patterns=include_variables,
          exclude_patterns=exclude_variables)

      clip_gradients_value = None
      if train_config.gradient_clipping_by_norm > 0:
        clip_gradients_value = train_config.gradient_clipping_by_norm

      if not use_tpu:
        for var in optimizer_summary_vars:
          tf.summary.scalar(var.op.name, var)
      summaries = [] if use_tpu else None
      if train_config.summarize_gradients:
        summaries = ['gradients', 'gradient_norm', 'global_gradient_norm']
      train_op = slim.optimizers.optimize_loss(
          loss=total_loss,
          global_step=global_step,
          learning_rate=None,
          clip_gradients=clip_gradients_value,
          optimizer=training_optimizer,
          update_ops=detection_model.updates(),
          variables=trainable_variables,
          summaries=summaries,
          name='')  # Preventing scope prefix on all variables.

    if mode == tf_estimator.ModeKeys.PREDICT:
      exported_output = exporter_lib.add_output_tensor_nodes(detections)
      export_outputs = {
          tf.saved_model.signature_constants.PREDICT_METHOD_NAME:
              tf_estimator.export.PredictOutput(exported_output)
      }

    eval_metric_ops = None
    scaffold = None
    if mode == tf_estimator.ModeKeys.EVAL:
      class_agnostic = (
          fields.DetectionResultFields.detection_classes not in detections)
      groundtruth = _prepare_groundtruth_for_eval(
          detection_model, class_agnostic,
          eval_input_config.max_number_of_boxes)
      use_original_images = fields.InputDataFields.original_image in features
      if use_original_images:
        eval_images = features[fields.InputDataFields.original_image]
        true_image_shapes = tf.slice(
            features[fields.InputDataFields.true_image_shape], [0, 0], [-1, 3])
        original_image_spatial_shapes = features[
            fields.InputDataFields.original_image_spatial_shape]
      else:
        eval_images = features[fields.InputDataFields.image]
        true_image_shapes = None
        original_image_spatial_shapes = None

      eval_dict = eval_util.result_dict_for_batched_example(
          eval_images,
          features[inputs.HASH_KEY],
          detections,
          groundtruth,
          class_agnostic=class_agnostic,
          scale_to_absolute=True,
          original_image_spatial_shapes=original_image_spatial_shapes,
          true_image_shapes=true_image_shapes)

      if fields.InputDataFields.image_additional_channels in features:
        eval_dict[fields.InputDataFields.image_additional_channels] = features[
            fields.InputDataFields.image_additional_channels]

      if class_agnostic:
        category_index = label_map_util.create_class_agnostic_category_index()
      else:
        category_index = label_map_util.create_category_index_from_labelmap(
            eval_input_config.label_map_path)
      vis_metric_ops = None
      if not use_tpu and use_original_images:
        keypoint_edges = [(kp.start, kp.end) for kp in eval_config.keypoint_edge
                         ]

        eval_metric_op_vis = vis_utils.VisualizeSingleFrameDetections(
            category_index,
            max_examples_to_draw=eval_config.num_visualizations,
            max_boxes_to_draw=eval_config.max_num_boxes_to_visualize,
            min_score_thresh=eval_config.min_score_threshold,
            use_normalized_coordinates=False,
            keypoint_edges=keypoint_edges or None)
        vis_metric_ops = eval_metric_op_vis.get_estimator_eval_metric_ops(
            eval_dict)

      # Eval metrics on a single example.
      eval_metric_ops = eval_util.get_eval_metric_ops_for_evaluators(
          eval_config, list(category_index.values()), eval_dict)
      for loss_key, loss_tensor in iter(losses_dict.items()):
        eval_metric_ops[loss_key] = tf.metrics.mean(loss_tensor)
      for var in optimizer_summary_vars:
        eval_metric_ops[var.op.name] = (var, tf.no_op())
      if vis_metric_ops is not None:
        eval_metric_ops.update(vis_metric_ops)
      eval_metric_ops = {str(k): v for k, v in eval_metric_ops.items()}

      if eval_config.use_moving_averages:
        variable_averages = tf.train.ExponentialMovingAverage(0.0)
        variables_to_restore = variable_averages.variables_to_restore()
        keep_checkpoint_every_n_hours = (
            train_config.keep_checkpoint_every_n_hours)
        saver = tf.train.Saver(
            variables_to_restore,
            keep_checkpoint_every_n_hours=keep_checkpoint_every_n_hours)
        scaffold = tf.train.Scaffold(saver=saver)

    # EVAL executes on CPU, so use regular non-TPU EstimatorSpec.
    if use_tpu and mode != tf_estimator.ModeKeys.EVAL:
      return tf_estimator.tpu.TPUEstimatorSpec(
          mode=mode,
          scaffold_fn=scaffold_fn,
          predictions=detections,
          loss=total_loss,
          train_op=train_op,
          eval_metrics=eval_metric_ops,
          export_outputs=export_outputs)
    else:
      if scaffold is None:
        keep_checkpoint_every_n_hours = (
            train_config.keep_checkpoint_every_n_hours)
        saver = tf.train.Saver(
            sharded=True,
            keep_checkpoint_every_n_hours=keep_checkpoint_every_n_hours,
            save_relative_paths=True)
        tf.add_to_collection(tf.GraphKeys.SAVERS, saver)
        scaffold = tf.train.Scaffold(saver=saver)
      return tf_estimator.EstimatorSpec(
          mode=mode,
          predictions=detections,
          loss=total_loss,
          train_op=train_op,
          eval_metric_ops=eval_metric_ops,
          export_outputs=export_outputs,
          scaffold=scaffold)