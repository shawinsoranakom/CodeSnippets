def _extract_prediction_tensors(model,
                                create_input_dict_fn,
                                ignore_groundtruth=False):
  """Restores the model in a tensorflow session.

  Args:
    model: model to perform predictions with.
    create_input_dict_fn: function to create input tensor dictionaries.
    ignore_groundtruth: whether groundtruth should be ignored.


  Returns:
    tensor_dict: A tensor dictionary with evaluations.
  """
  input_dict = create_input_dict_fn()
  batch = None
  if 'batch' in input_dict:
    batch = input_dict.pop('batch')
  else:
    prefetch_queue = prefetcher.prefetch(input_dict, capacity=500)
    input_dict = prefetch_queue.dequeue()
    # consistent format for images and videos
    for key, value in input_dict.iteritems():
      input_dict[key] = (value,)

  detections = _create_detection_op(model, input_dict, batch)

  # Print out anaylsis of the model.
  contrib_tfprof.model_analyzer.print_model_analysis(
      tf.get_default_graph(),
      tfprof_options=contrib_tfprof.model_analyzer
      .TRAINABLE_VARS_PARAMS_STAT_OPTIONS)
  contrib_tfprof.model_analyzer.print_model_analysis(
      tf.get_default_graph(),
      tfprof_options=contrib_tfprof.model_analyzer.FLOAT_OPS_OPTIONS)

  num_frames = len(input_dict[fields.InputDataFields.image])
  ret = []
  for i in range(num_frames):
    original_image = tf.expand_dims(input_dict[fields.InputDataFields.image][i],
                                    0)
    groundtruth = None
    if not ignore_groundtruth:
      groundtruth = {
          fields.InputDataFields.groundtruth_boxes:
              input_dict[fields.InputDataFields.groundtruth_boxes][i],
          fields.InputDataFields.groundtruth_classes:
              input_dict[fields.InputDataFields.groundtruth_classes][i],
      }
      optional_keys = (
          fields.InputDataFields.groundtruth_area,
          fields.InputDataFields.groundtruth_is_crowd,
          fields.InputDataFields.groundtruth_difficult,
          fields.InputDataFields.groundtruth_group_of,
      )
      for opt_key in optional_keys:
        if opt_key in input_dict:
          groundtruth[opt_key] = input_dict[opt_key][i]
      if fields.DetectionResultFields.detection_masks in detections:
        groundtruth[fields.InputDataFields.groundtruth_instance_masks] = (
            input_dict[fields.InputDataFields.groundtruth_instance_masks][i])

    detections_frame = {
        key: tf.expand_dims(value[i], 0)
        for key, value in detections.iteritems()
    }

    source_id = (
        batch.key[0] if batch is not None else
        input_dict[fields.InputDataFields.source_id][i])
    ret.append(
        eval_util.result_dict_for_single_example(
            original_image,
            source_id,
            detections_frame,
            groundtruth,
            class_agnostic=(fields.DetectionResultFields.detection_classes
                            not in detections),
            scale_to_absolute=True))
  return ret