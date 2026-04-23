def extract_features(images,
                     output_stride=8,
                     multi_grid=None,
                     depth_multiplier=1.0,
                     divisible_by=None,
                     final_endpoint=None,
                     model_variant=None,
                     weight_decay=0.0001,
                     reuse=None,
                     is_training=False,
                     fine_tune_batch_norm=False,
                     regularize_depthwise=False,
                     preprocess_images=True,
                     preprocessed_images_dtype=tf.float32,
                     num_classes=None,
                     global_pool=False,
                     nas_architecture_options=None,
                     nas_training_hyper_parameters=None,
                     use_bounded_activation=False):
  """Extracts features by the particular model_variant.

  Args:
    images: A tensor of size [batch, height, width, channels].
    output_stride: The ratio of input to output spatial resolution.
    multi_grid: Employ a hierarchy of different atrous rates within network.
    depth_multiplier: Float multiplier for the depth (number of channels)
      for all convolution ops used in MobileNet.
    divisible_by: None (use default setting) or an integer that ensures all
      layers # channels will be divisible by this number. Used in MobileNet.
    final_endpoint: The MobileNet endpoint to construct the network up to.
    model_variant: Model variant for feature extraction.
    weight_decay: The weight decay for model variables.
    reuse: Reuse the model variables or not.
    is_training: Is training or not.
    fine_tune_batch_norm: Fine-tune the batch norm parameters or not.
    regularize_depthwise: Whether or not apply L2-norm regularization on the
      depthwise convolution weights.
    preprocess_images: Performs preprocessing on images or not. Defaults to
      True. Set to False if preprocessing will be done by other functions. We
      supprot two types of preprocessing: (1) Mean pixel substraction and (2)
      Pixel values normalization to be [-1, 1].
    preprocessed_images_dtype: The type after the preprocessing function.
    num_classes: Number of classes for image classification task. Defaults
      to None for dense prediction tasks.
    global_pool: Global pooling for image classification task. Defaults to
      False, since dense prediction tasks do not use this.
    nas_architecture_options: A dictionary storing NAS architecture options.
      It is either None or its kerys are:
      - `nas_stem_output_num_conv_filters`: Number of filters of the NAS stem
        output tensor.
      - `nas_use_classification_head`: Boolean, use image classification head.
    nas_training_hyper_parameters: A dictionary storing hyper-parameters for
      training nas models. It is either None or its keys are:
      - `drop_path_keep_prob`: Probability to keep each path in the cell when
        training.
      - `total_training_steps`: Total training steps to help drop path
        probability calculation.
    use_bounded_activation: Whether or not to use bounded activations. Bounded
      activations better lend themselves to quantized inference. Currently,
      bounded activation is only used in xception model.

  Returns:
    features: A tensor of size [batch, feature_height, feature_width,
      feature_channels], where feature_height/feature_width are determined
      by the images height/width and output_stride.
    end_points: A dictionary from components of the network to the corresponding
      activation.

  Raises:
    ValueError: Unrecognized model variant.
  """
  if 'resnet' in model_variant:
    arg_scope = arg_scopes_map[model_variant](
        weight_decay=weight_decay,
        batch_norm_decay=0.95,
        batch_norm_epsilon=1e-5,
        batch_norm_scale=True)
    features, end_points = get_network(
        model_variant, preprocess_images, preprocessed_images_dtype, arg_scope)(
            inputs=images,
            num_classes=num_classes,
            is_training=(is_training and fine_tune_batch_norm),
            global_pool=global_pool,
            output_stride=output_stride,
            multi_grid=multi_grid,
            reuse=reuse,
            scope=name_scope[model_variant])
  elif 'xception' in model_variant:
    arg_scope = arg_scopes_map[model_variant](
        weight_decay=weight_decay,
        batch_norm_decay=0.9997,
        batch_norm_epsilon=1e-3,
        batch_norm_scale=True,
        regularize_depthwise=regularize_depthwise,
        use_bounded_activation=use_bounded_activation)
    features, end_points = get_network(
        model_variant, preprocess_images, preprocessed_images_dtype, arg_scope)(
            inputs=images,
            num_classes=num_classes,
            is_training=(is_training and fine_tune_batch_norm),
            global_pool=global_pool,
            output_stride=output_stride,
            regularize_depthwise=regularize_depthwise,
            multi_grid=multi_grid,
            reuse=reuse,
            scope=name_scope[model_variant])
  elif 'mobilenet' in model_variant or model_variant.startswith('mnas'):
    arg_scope = arg_scopes_map[model_variant](
        is_training=(is_training and fine_tune_batch_norm),
        weight_decay=weight_decay)
    features, end_points = get_network(
        model_variant, preprocess_images, preprocessed_images_dtype, arg_scope)(
            inputs=images,
            depth_multiplier=depth_multiplier,
            divisible_by=divisible_by,
            output_stride=output_stride,
            reuse=reuse,
            scope=name_scope[model_variant],
            final_endpoint=final_endpoint)
  elif model_variant.startswith('nas'):
    arg_scope = arg_scopes_map[model_variant](
        weight_decay=weight_decay,
        batch_norm_decay=0.9997,
        batch_norm_epsilon=1e-3)
    features, end_points = get_network(
        model_variant, preprocess_images, preprocessed_images_dtype, arg_scope)(
            inputs=images,
            num_classes=num_classes,
            is_training=(is_training and fine_tune_batch_norm),
            global_pool=global_pool,
            output_stride=output_stride,
            nas_architecture_options=nas_architecture_options,
            nas_training_hyper_parameters=nas_training_hyper_parameters,
            reuse=reuse,
            scope=name_scope[model_variant])
  else:
    raise ValueError('Unknown model variant %s.' % model_variant)

  return features, end_points