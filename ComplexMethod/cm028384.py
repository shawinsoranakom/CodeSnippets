def multi_scale_logits(images,
                       model_options,
                       image_pyramid,
                       weight_decay=0.0001,
                       is_training=False,
                       fine_tune_batch_norm=False,
                       nas_training_hyper_parameters=None):
  """Gets the logits for multi-scale inputs.

  The returned logits are all downsampled (due to max-pooling layers)
  for both training and evaluation.

  Args:
    images: A tensor of size [batch, height, width, channels].
    model_options: A ModelOptions instance to configure models.
    image_pyramid: Input image scales for multi-scale feature extraction.
    weight_decay: The weight decay for model variables.
    is_training: Is training or not.
    fine_tune_batch_norm: Fine-tune the batch norm parameters or not.
    nas_training_hyper_parameters: A dictionary storing hyper-parameters for
      training nas models. Its keys are:
      - `drop_path_keep_prob`: Probability to keep each path in the cell when
        training.
      - `total_training_steps`: Total training steps to help drop path
        probability calculation.

  Returns:
    outputs_to_scales_to_logits: A map of maps from output_type (e.g.,
      semantic prediction) to a dictionary of multi-scale logits names to
      logits. For each output_type, the dictionary has keys which
      correspond to the scales and values which correspond to the logits.
      For example, if `scales` equals [1.0, 1.5], then the keys would
      include 'merged_logits', 'logits_1.00' and 'logits_1.50'.

  Raises:
    ValueError: If model_options doesn't specify crop_size and its
      add_image_level_feature = True, since add_image_level_feature requires
      crop_size information.
  """
  # Setup default values.
  if not image_pyramid:
    image_pyramid = [1.0]
  crop_height = (
      model_options.crop_size[0]
      if model_options.crop_size else tf.shape(images)[1])
  crop_width = (
      model_options.crop_size[1]
      if model_options.crop_size else tf.shape(images)[2])
  if model_options.image_pooling_crop_size:
    image_pooling_crop_height = model_options.image_pooling_crop_size[0]
    image_pooling_crop_width = model_options.image_pooling_crop_size[1]

  # Compute the height, width for the output logits.
  if model_options.decoder_output_stride:
    logits_output_stride = min(model_options.decoder_output_stride)
  else:
    logits_output_stride = model_options.output_stride

  logits_height = scale_dimension(
      crop_height,
      max(1.0, max(image_pyramid)) / logits_output_stride)
  logits_width = scale_dimension(
      crop_width,
      max(1.0, max(image_pyramid)) / logits_output_stride)

  # Compute the logits for each scale in the image pyramid.
  outputs_to_scales_to_logits = {
      k: {}
      for k in model_options.outputs_to_num_classes
  }

  num_channels = images.get_shape().as_list()[-1]

  for image_scale in image_pyramid:
    if image_scale != 1.0:
      scaled_height = scale_dimension(crop_height, image_scale)
      scaled_width = scale_dimension(crop_width, image_scale)
      scaled_crop_size = [scaled_height, scaled_width]
      scaled_images = _resize_bilinear(images, scaled_crop_size, images.dtype)
      if model_options.crop_size:
        scaled_images.set_shape(
            [None, scaled_height, scaled_width, num_channels])
      # Adjust image_pooling_crop_size accordingly.
      scaled_image_pooling_crop_size = None
      if model_options.image_pooling_crop_size:
        scaled_image_pooling_crop_size = [
            scale_dimension(image_pooling_crop_height, image_scale),
            scale_dimension(image_pooling_crop_width, image_scale)]
    else:
      scaled_crop_size = model_options.crop_size
      scaled_images = images
      scaled_image_pooling_crop_size = model_options.image_pooling_crop_size

    updated_options = model_options._replace(
        crop_size=scaled_crop_size,
        image_pooling_crop_size=scaled_image_pooling_crop_size)
    outputs_to_logits = _get_logits(
        scaled_images,
        updated_options,
        weight_decay=weight_decay,
        reuse=tf.AUTO_REUSE,
        is_training=is_training,
        fine_tune_batch_norm=fine_tune_batch_norm,
        nas_training_hyper_parameters=nas_training_hyper_parameters)

    # Resize the logits to have the same dimension before merging.
    for output in sorted(outputs_to_logits):
      outputs_to_logits[output] = _resize_bilinear(
          outputs_to_logits[output], [logits_height, logits_width],
          outputs_to_logits[output].dtype)

    # Return when only one input scale.
    if len(image_pyramid) == 1:
      for output in sorted(model_options.outputs_to_num_classes):
        outputs_to_scales_to_logits[output][
            MERGED_LOGITS_SCOPE] = outputs_to_logits[output]
      return outputs_to_scales_to_logits

    # Save logits to the output map.
    for output in sorted(model_options.outputs_to_num_classes):
      outputs_to_scales_to_logits[output][
          'logits_%.2f' % image_scale] = outputs_to_logits[output]

  # Merge the logits from all the multi-scale inputs.
  for output in sorted(model_options.outputs_to_num_classes):
    # Concatenate the multi-scale logits for each output type.
    all_logits = [
        tf.expand_dims(logits, axis=4)
        for logits in outputs_to_scales_to_logits[output].values()
    ]
    all_logits = tf.concat(all_logits, 4)
    merge_fn = (
        tf.reduce_max
        if model_options.merge_method == 'max' else tf.reduce_mean)
    outputs_to_scales_to_logits[output][MERGED_LOGITS_SCOPE] = merge_fn(
        all_logits, axis=4)

  return outputs_to_scales_to_logits