def extract_features(images,
                     model_options,
                     weight_decay=0.0001,
                     reuse=None,
                     is_training=False,
                     fine_tune_batch_norm=False,
                     nas_training_hyper_parameters=None):
  """Extracts features by the particular model_variant.

  Args:
    images: A tensor of size [batch, height, width, channels].
    model_options: A ModelOptions instance to configure models.
    weight_decay: The weight decay for model variables.
    reuse: Reuse the model variables or not.
    is_training: Is training or not.
    fine_tune_batch_norm: Fine-tune the batch norm parameters or not.
    nas_training_hyper_parameters: A dictionary storing hyper-parameters for
      training nas models. Its keys are:
      - `drop_path_keep_prob`: Probability to keep each path in the cell when
        training.
      - `total_training_steps`: Total training steps to help drop path
        probability calculation.

  Returns:
    concat_logits: A tensor of size [batch, feature_height, feature_width,
      feature_channels], where feature_height/feature_width are determined by
      the images height/width and output_stride.
    end_points: A dictionary from components of the network to the corresponding
      activation.
  """
  features, end_points = feature_extractor.extract_features(
      images,
      output_stride=model_options.output_stride,
      multi_grid=model_options.multi_grid,
      model_variant=model_options.model_variant,
      depth_multiplier=model_options.depth_multiplier,
      divisible_by=model_options.divisible_by,
      weight_decay=weight_decay,
      reuse=reuse,
      is_training=is_training,
      preprocessed_images_dtype=model_options.preprocessed_images_dtype,
      fine_tune_batch_norm=fine_tune_batch_norm,
      nas_architecture_options=model_options.nas_architecture_options,
      nas_training_hyper_parameters=nas_training_hyper_parameters,
      use_bounded_activation=model_options.use_bounded_activation)

  if not model_options.aspp_with_batch_norm:
    return features, end_points
  else:
    if model_options.dense_prediction_cell_config is not None:
      tf.logging.info('Using dense prediction cell config.')
      dense_prediction_layer = dense_prediction_cell.DensePredictionCell(
          config=model_options.dense_prediction_cell_config,
          hparams={
              'conv_rate_multiplier': 16 // model_options.output_stride,
          })
      concat_logits = dense_prediction_layer.build_cell(
          features,
          output_stride=model_options.output_stride,
          crop_size=model_options.crop_size,
          image_pooling_crop_size=model_options.image_pooling_crop_size,
          weight_decay=weight_decay,
          reuse=reuse,
          is_training=is_training,
          fine_tune_batch_norm=fine_tune_batch_norm)
      return concat_logits, end_points
    else:
      # The following codes employ the DeepLabv3 ASPP module. Note that we
      # could express the ASPP module as one particular dense prediction
      # cell architecture. We do not do so but leave the following codes
      # for backward compatibility.
      batch_norm_params = utils.get_batch_norm_params(
          decay=0.9997,
          epsilon=1e-5,
          scale=True,
          is_training=(is_training and fine_tune_batch_norm),
          sync_batch_norm_method=model_options.sync_batch_norm_method)
      batch_norm = utils.get_batch_norm_fn(
          model_options.sync_batch_norm_method)
      activation_fn = (
          tf.nn.relu6 if model_options.use_bounded_activation else tf.nn.relu)
      with slim.arg_scope(
          [slim.conv2d, slim.separable_conv2d],
          weights_regularizer=slim.l2_regularizer(weight_decay),
          activation_fn=activation_fn,
          normalizer_fn=batch_norm,
          padding='SAME',
          stride=1,
          reuse=reuse):
        with slim.arg_scope([batch_norm], **batch_norm_params):
          depth = model_options.aspp_convs_filters
          branch_logits = []

          if model_options.add_image_level_feature:
            if model_options.crop_size is not None:
              image_pooling_crop_size = model_options.image_pooling_crop_size
              # If image_pooling_crop_size is not specified, use crop_size.
              if image_pooling_crop_size is None:
                image_pooling_crop_size = model_options.crop_size
              pool_height = scale_dimension(
                  image_pooling_crop_size[0],
                  1. / model_options.output_stride)
              pool_width = scale_dimension(
                  image_pooling_crop_size[1],
                  1. / model_options.output_stride)
              image_feature = slim.avg_pool2d(
                  features, [pool_height, pool_width],
                  model_options.image_pooling_stride, padding='VALID')
              resize_height = scale_dimension(
                  model_options.crop_size[0],
                  1. / model_options.output_stride)
              resize_width = scale_dimension(
                  model_options.crop_size[1],
                  1. / model_options.output_stride)
            else:
              # If crop_size is None, we simply do global pooling.
              pool_height = tf.shape(features)[1]
              pool_width = tf.shape(features)[2]
              image_feature = tf.reduce_mean(
                  features, axis=[1, 2], keepdims=True)
              resize_height = pool_height
              resize_width = pool_width
            image_feature_activation_fn = tf.nn.relu
            image_feature_normalizer_fn = batch_norm
            if model_options.aspp_with_squeeze_and_excitation:
              image_feature_activation_fn = tf.nn.sigmoid
              if model_options.image_se_uses_qsigmoid:
                image_feature_activation_fn = utils.q_sigmoid
              image_feature_normalizer_fn = None
            image_feature = slim.conv2d(
                image_feature, depth, 1,
                activation_fn=image_feature_activation_fn,
                normalizer_fn=image_feature_normalizer_fn,
                scope=IMAGE_POOLING_SCOPE)
            image_feature = _resize_bilinear(
                image_feature,
                [resize_height, resize_width],
                image_feature.dtype)
            # Set shape for resize_height/resize_width if they are not Tensor.
            if isinstance(resize_height, tf.Tensor):
              resize_height = None
            if isinstance(resize_width, tf.Tensor):
              resize_width = None
            image_feature.set_shape([None, resize_height, resize_width, depth])
            if not model_options.aspp_with_squeeze_and_excitation:
              branch_logits.append(image_feature)

          # Employ a 1x1 convolution.
          branch_logits.append(slim.conv2d(features, depth, 1,
                                           scope=ASPP_SCOPE + str(0)))

          if model_options.atrous_rates:
            # Employ 3x3 convolutions with different atrous rates.
            for i, rate in enumerate(model_options.atrous_rates, 1):
              scope = ASPP_SCOPE + str(i)
              if model_options.aspp_with_separable_conv:
                aspp_features = split_separable_conv2d(
                    features,
                    filters=depth,
                    rate=rate,
                    weight_decay=weight_decay,
                    scope=scope)
              else:
                aspp_features = slim.conv2d(
                    features, depth, 3, rate=rate, scope=scope)
              branch_logits.append(aspp_features)

          # Merge branch logits.
          concat_logits = tf.concat(branch_logits, 3)
          if model_options.aspp_with_concat_projection:
            concat_logits = slim.conv2d(
                concat_logits, depth, 1, scope=CONCAT_PROJECTION_SCOPE)
            concat_logits = slim.dropout(
                concat_logits,
                keep_prob=0.9,
                is_training=is_training,
                scope=CONCAT_PROJECTION_SCOPE + '_dropout')
          if (model_options.add_image_level_feature and
              model_options.aspp_with_squeeze_and_excitation):
            concat_logits *= image_feature

          return concat_logits, end_points