def eager_eval_loop(
    detection_model,
    configs,
    eval_dataset,
    use_tpu=False,
    postprocess_on_cpu=False,
    global_step=None,
    ):
  """Evaluate the model eagerly on the evaluation dataset.

  This method will compute the evaluation metrics specified in the configs on
  the entire evaluation dataset, then return the metrics. It will also log
  the metrics to TensorBoard.

  Args:
    detection_model: A DetectionModel (based on Keras) to evaluate.
    configs: Object detection configs that specify the evaluators that should
      be used, as well as whether regularization loss should be included and
      if bfloat16 should be used on TPUs.
    eval_dataset: Dataset containing evaluation data.
    use_tpu: Whether a TPU is being used to execute the model for evaluation.
    postprocess_on_cpu: Whether model postprocessing should happen on
      the CPU when using a TPU to execute the model.
    global_step: A variable containing the training step this model was trained
      to. Used for logging purposes.

  Returns:
    A dict of evaluation metrics representing the results of this evaluation.
  """
  del postprocess_on_cpu
  train_config = configs['train_config']
  eval_input_config = configs['eval_input_config']
  eval_config = configs['eval_config']
  add_regularization_loss = train_config.add_regularization_loss

  is_training = False
  detection_model._is_training = is_training  # pylint: disable=protected-access
  tf.keras.backend.set_learning_phase(is_training)

  evaluator_options = eval_util.evaluator_options_from_eval_config(
      eval_config)
  batch_size = eval_config.batch_size

  class_agnostic_category_index = (
      label_map_util.create_class_agnostic_category_index())
  class_agnostic_evaluators = eval_util.get_evaluators(
      eval_config,
      list(class_agnostic_category_index.values()),
      evaluator_options)

  class_aware_evaluators = None
  if eval_input_config.label_map_path:
    class_aware_category_index = (
        label_map_util.create_category_index_from_labelmap(
            eval_input_config.label_map_path))
    class_aware_evaluators = eval_util.get_evaluators(
        eval_config,
        list(class_aware_category_index.values()),
        evaluator_options)

  evaluators = None
  loss_metrics = {}

  @tf.function
  def compute_eval_dict(features, labels):
    """Compute the evaluation result on an image."""
    # For evaling on train data, it is necessary to check whether groundtruth
    # must be unpadded.
    boxes_shape = (
        labels[fields.InputDataFields.groundtruth_boxes].get_shape().as_list())
    unpad_groundtruth_tensors = (boxes_shape[1] is not None
                                 and not use_tpu
                                 and batch_size == 1)
    groundtruth_dict = labels
    labels = model_lib.unstack_batch(
        labels, unpad_groundtruth_tensors=unpad_groundtruth_tensors)

    losses_dict, prediction_dict = _compute_losses_and_predictions_dicts(
        detection_model, features, labels, training_step=None,
        add_regularization_loss=add_regularization_loss)
    prediction_dict = detection_model.postprocess(
        prediction_dict, features[fields.InputDataFields.true_image_shape])
    eval_features = {
        fields.InputDataFields.image:
            features[fields.InputDataFields.image],
        fields.InputDataFields.original_image:
            features[fields.InputDataFields.original_image],
        fields.InputDataFields.original_image_spatial_shape:
            features[fields.InputDataFields.original_image_spatial_shape],
        fields.InputDataFields.true_image_shape:
            features[fields.InputDataFields.true_image_shape],
        inputs.HASH_KEY: features[inputs.HASH_KEY],
    }
    return losses_dict, prediction_dict, groundtruth_dict, eval_features

  agnostic_categories = label_map_util.create_class_agnostic_category_index()
  per_class_categories = label_map_util.create_category_index_from_labelmap(
      eval_input_config.label_map_path)
  keypoint_edges = [
      (kp.start, kp.end) for kp in eval_config.keypoint_edge]

  strategy = tf.compat.v2.distribute.get_strategy()

  for i, (features, labels) in enumerate(eval_dataset):
    try:
      (losses_dict, prediction_dict, groundtruth_dict,
       eval_features) = strategy.run(
           compute_eval_dict, args=(features, labels))
    except Exception as exc:  # pylint:disable=broad-except
      tf.logging.info('Encountered %s exception.', exc)
      tf.logging.info('A replica probably exhausted all examples. Skipping '
                      'pending examples on other replicas.')
      break
    (local_prediction_dict, local_groundtruth_dict,
     local_eval_features) = tf.nest.map_structure(
         strategy.experimental_local_results,
         [prediction_dict, groundtruth_dict, eval_features])
    local_prediction_dict = concat_replica_results(local_prediction_dict)
    local_groundtruth_dict = concat_replica_results(local_groundtruth_dict)
    local_eval_features = concat_replica_results(local_eval_features)

    eval_dict, class_agnostic = prepare_eval_dict(local_prediction_dict,
                                                  local_groundtruth_dict,
                                                  local_eval_features)
    for loss_key, loss_tensor in iter(losses_dict.items()):
      losses_dict[loss_key] = strategy.reduce(tf.distribute.ReduceOp.MEAN,
                                              loss_tensor, None)
    if class_agnostic:
      category_index = agnostic_categories
    else:
      category_index = per_class_categories

    if i % 100 == 0:
      tf.logging.info('Finished eval step %d', i)

    use_original_images = fields.InputDataFields.original_image in features
    if (use_original_images and i < eval_config.num_visualizations):
      sbys_image_list = vutils.draw_side_by_side_evaluation_image(
          eval_dict,
          category_index=category_index,
          max_boxes_to_draw=eval_config.max_num_boxes_to_visualize,
          min_score_thresh=eval_config.min_score_threshold,
          use_normalized_coordinates=False,
          keypoint_edges=keypoint_edges or None)
      for j, sbys_image in enumerate(sbys_image_list):
        tf.compat.v2.summary.image(
            name='eval_side_by_side_{}_{}'.format(i, j),
            step=global_step,
            data=sbys_image,
            max_outputs=eval_config.num_visualizations)
      if eval_util.has_densepose(eval_dict):
        dp_image_list = vutils.draw_densepose_visualizations(
            eval_dict)
        for j, dp_image in enumerate(dp_image_list):
          tf.compat.v2.summary.image(
              name='densepose_detections_{}_{}'.format(i, j),
              step=global_step,
              data=dp_image,
              max_outputs=eval_config.num_visualizations)

    if evaluators is None:
      if class_agnostic:
        evaluators = class_agnostic_evaluators
      else:
        evaluators = class_aware_evaluators

    for evaluator in evaluators:
      evaluator.add_eval_dict(eval_dict)

    for loss_key, loss_tensor in iter(losses_dict.items()):
      if loss_key not in loss_metrics:
        loss_metrics[loss_key] = []
      loss_metrics[loss_key].append(loss_tensor)

  eval_metrics = {}

  for evaluator in evaluators:
    eval_metrics.update(evaluator.evaluate())
  for loss_key in loss_metrics:
    eval_metrics[loss_key] = tf.reduce_mean(loss_metrics[loss_key])

  eval_metrics = {str(k): v for k, v in eval_metrics.items()}
  tf.logging.info('Eval metrics at step %d', global_step.numpy())
  for k in eval_metrics:
    tf.compat.v2.summary.scalar(k, eval_metrics[k], step=global_step)
    tf.logging.info('\t+ %s: %f', k, eval_metrics[k])
  return eval_metrics