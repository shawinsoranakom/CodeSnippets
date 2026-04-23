def evaluate(create_input_dict_fn, create_model_fn, eval_config, categories,
             checkpoint_dir, eval_dir, graph_hook_fn=None, evaluator_list=None):
  """Evaluation function for detection models.

  Args:
    create_input_dict_fn: a function to create a tensor input dictionary.
    create_model_fn: a function that creates a DetectionModel.
    eval_config: a eval_pb2.EvalConfig protobuf.
    categories: a list of category dictionaries. Each dict in the list should
                have an integer 'id' field and string 'name' field.
    checkpoint_dir: directory to load the checkpoints to evaluate from.
    eval_dir: directory to write evaluation metrics summary to.
    graph_hook_fn: Optional function that is called after the training graph is
      completely built. This is helpful to perform additional changes to the
      training graph such as optimizing batchnorm. The function should modify
      the default graph.
    evaluator_list: Optional list of instances of DetectionEvaluator. If not
      given, this list of metrics is created according to the eval_config.

  Returns:
    metrics: A dictionary containing metric names and values from the latest
      run.
  """

  model = create_model_fn()

  if eval_config.ignore_groundtruth and not eval_config.export_path:
    logging.fatal('If ignore_groundtruth=True then an export_path is '
                  'required. Aborting!!!')

  tensor_dict, losses_dict = _extract_predictions_and_losses(
      model=model,
      create_input_dict_fn=create_input_dict_fn,
      ignore_groundtruth=eval_config.ignore_groundtruth)

  def _process_batch(tensor_dict, sess, batch_index, counters,
                     losses_dict=None):
    """Evaluates tensors in tensor_dict, losses_dict and visualizes examples.

    This function calls sess.run on tensor_dict, evaluating the original_image
    tensor only on the first K examples and visualizing detections overlaid
    on this original_image.

    Args:
      tensor_dict: a dictionary of tensors
      sess: tensorflow session
      batch_index: the index of the batch amongst all batches in the run.
      counters: a dictionary holding 'success' and 'skipped' fields which can
        be updated to keep track of number of successful and failed runs,
        respectively.  If these fields are not updated, then the success/skipped
        counter values shown at the end of evaluation will be incorrect.
      losses_dict: Optional dictonary of scalar loss tensors.

    Returns:
      result_dict: a dictionary of numpy arrays
      result_losses_dict: a dictionary of scalar losses. This is empty if input
        losses_dict is None.
    """
    try:
      if not losses_dict:
        losses_dict = {}
      result_dict, result_losses_dict = sess.run([tensor_dict, losses_dict])
      counters['success'] += 1
    except tf.errors.InvalidArgumentError:
      logging.info('Skipping image')
      counters['skipped'] += 1
      return {}, {}
    global_step = tf.train.global_step(sess, tf.train.get_global_step())
    if batch_index < eval_config.num_visualizations:
      tag = 'image-{}'.format(batch_index)
      eval_util.visualize_detection_results(
          result_dict,
          tag,
          global_step,
          categories=categories,
          summary_dir=eval_dir,
          export_dir=eval_config.visualization_export_dir,
          show_groundtruth=eval_config.visualize_groundtruth_boxes,
          groundtruth_box_visualization_color=eval_config.
          groundtruth_box_visualization_color,
          min_score_thresh=eval_config.min_score_threshold,
          max_num_predictions=eval_config.max_num_boxes_to_visualize,
          skip_scores=eval_config.skip_scores,
          skip_labels=eval_config.skip_labels,
          keep_image_id_for_visualization_export=eval_config.
          keep_image_id_for_visualization_export)
    return result_dict, result_losses_dict

  if graph_hook_fn: graph_hook_fn()

  variables_to_restore = tf.global_variables()
  global_step = tf.train.get_or_create_global_step()
  variables_to_restore.append(global_step)

  if eval_config.use_moving_averages:
    variable_averages = tf.train.ExponentialMovingAverage(0.0)
    variables_to_restore = variable_averages.variables_to_restore()
  saver = tf.train.Saver(variables_to_restore)

  def _restore_latest_checkpoint(sess):
    latest_checkpoint = tf.train.latest_checkpoint(checkpoint_dir)
    saver.restore(sess, latest_checkpoint)

  if not evaluator_list:
    evaluator_list = get_evaluators(eval_config, categories)

  metrics = eval_util.repeated_checkpoint_run(
      tensor_dict=tensor_dict,
      summary_dir=eval_dir,
      evaluators=evaluator_list,
      batch_processor=_process_batch,
      checkpoint_dirs=[checkpoint_dir],
      variables_to_restore=None,
      restore_fn=_restore_latest_checkpoint,
      num_batches=eval_config.num_examples,
      eval_interval_secs=eval_config.eval_interval_secs,
      max_number_of_evaluations=(1 if eval_config.ignore_groundtruth else
                                 eval_config.max_evals
                                 if eval_config.max_evals else None),
      master=eval_config.eval_master,
      save_graph=eval_config.save_graph,
      save_graph_dir=(eval_dir if eval_config.save_graph else ''),
      losses_dict=losses_dict,
      eval_export_path=eval_config.export_path)

  return metrics