def refine_by_decoder(features,
                      end_points,
                      crop_size=None,
                      decoder_output_stride=None,
                      decoder_use_separable_conv=False,
                      decoder_use_sum_merge=False,
                      decoder_filters=256,
                      decoder_output_is_logits=False,
                      model_variant=None,
                      weight_decay=0.0001,
                      reuse=None,
                      is_training=False,
                      fine_tune_batch_norm=False,
                      use_bounded_activation=False,
                      sync_batch_norm_method='None'):
  """Adds the decoder to obtain sharper segmentation results.

  Args:
    features: A tensor of size [batch, features_height, features_width,
      features_channels].
    end_points: A dictionary from components of the network to the corresponding
      activation.
    crop_size: A tuple [crop_height, crop_width] specifying whole patch crop
      size.
    decoder_output_stride: A list of integers specifying the output stride of
      low-level features used in the decoder module.
    decoder_use_separable_conv: Employ separable convolution for decoder or not.
    decoder_use_sum_merge: Boolean, decoder uses simple sum merge or not.
    decoder_filters: Integer, decoder filter size.
    decoder_output_is_logits: Boolean, using decoder output as logits or not.
    model_variant: Model variant for feature extraction.
    weight_decay: The weight decay for model variables.
    reuse: Reuse the model variables or not.
    is_training: Is training or not.
    fine_tune_batch_norm: Fine-tune the batch norm parameters or not.
    use_bounded_activation: Whether or not to use bounded activations. Bounded
      activations better lend themselves to quantized inference.
    sync_batch_norm_method: String, method used to sync batch norm. Currently
     only support `None` (no sync batch norm) and `tpu` (use tpu code to
     sync batch norm).

  Returns:
    Decoder output with size [batch, decoder_height, decoder_width,
      decoder_channels].

  Raises:
    ValueError: If crop_size is None.
  """
  if crop_size is None:
    raise ValueError('crop_size must be provided when using decoder.')
  batch_norm_params = utils.get_batch_norm_params(
      decay=0.9997,
      epsilon=1e-5,
      scale=True,
      is_training=(is_training and fine_tune_batch_norm),
      sync_batch_norm_method=sync_batch_norm_method)
  batch_norm = utils.get_batch_norm_fn(sync_batch_norm_method)
  decoder_depth = decoder_filters
  projected_filters = 48
  if decoder_use_sum_merge:
    # When using sum merge, the projected filters must be equal to decoder
    # filters.
    projected_filters = decoder_filters
  if decoder_output_is_logits:
    # Overwrite the setting when decoder output is logits.
    activation_fn = None
    normalizer_fn = None
    conv2d_kernel = 1
    # Use original conv instead of separable conv.
    decoder_use_separable_conv = False
  else:
    # Default setting when decoder output is not logits.
    activation_fn = tf.nn.relu6 if use_bounded_activation else tf.nn.relu
    normalizer_fn = batch_norm
    conv2d_kernel = 3
  with slim.arg_scope(
      [slim.conv2d, slim.separable_conv2d],
      weights_regularizer=slim.l2_regularizer(weight_decay),
      activation_fn=activation_fn,
      normalizer_fn=normalizer_fn,
      padding='SAME',
      stride=1,
      reuse=reuse):
    with slim.arg_scope([batch_norm], **batch_norm_params):
      with tf.variable_scope(DECODER_SCOPE, DECODER_SCOPE, [features]):
        decoder_features = features
        decoder_stage = 0
        scope_suffix = ''
        for output_stride in decoder_output_stride:
          feature_list = feature_extractor.networks_to_feature_maps[
              model_variant][
                  feature_extractor.DECODER_END_POINTS][output_stride]
          # If only one decoder stage, we do not change the scope name in
          # order for backward compactibility.
          if decoder_stage:
            scope_suffix = '_{}'.format(decoder_stage)
          for i, name in enumerate(feature_list):
            decoder_features_list = [decoder_features]
            # MobileNet and NAS variants use different naming convention.
            if ('mobilenet' in model_variant or
                model_variant.startswith('mnas') or
                model_variant.startswith('nas')):
              feature_name = name
            else:
              feature_name = '{}/{}'.format(
                  feature_extractor.name_scope[model_variant], name)
            decoder_features_list.append(
                slim.conv2d(
                    end_points[feature_name],
                    projected_filters,
                    1,
                    scope='feature_projection' + str(i) + scope_suffix))
            # Determine the output size.
            decoder_height = scale_dimension(crop_size[0], 1.0 / output_stride)
            decoder_width = scale_dimension(crop_size[1], 1.0 / output_stride)
            # Resize to decoder_height/decoder_width.
            for j, feature in enumerate(decoder_features_list):
              decoder_features_list[j] = _resize_bilinear(
                  feature, [decoder_height, decoder_width], feature.dtype)
              h = (None if isinstance(decoder_height, tf.Tensor)
                   else decoder_height)
              w = (None if isinstance(decoder_width, tf.Tensor)
                   else decoder_width)
              decoder_features_list[j].set_shape([None, h, w, None])
            if decoder_use_sum_merge:
              decoder_features = _decoder_with_sum_merge(
                  decoder_features_list,
                  decoder_depth,
                  conv2d_kernel=conv2d_kernel,
                  decoder_use_separable_conv=decoder_use_separable_conv,
                  weight_decay=weight_decay,
                  scope_suffix=scope_suffix)
            else:
              if not decoder_use_separable_conv:
                scope_suffix = str(i) + scope_suffix
              decoder_features = _decoder_with_concat_merge(
                  decoder_features_list,
                  decoder_depth,
                  decoder_use_separable_conv=decoder_use_separable_conv,
                  weight_decay=weight_decay,
                  scope_suffix=scope_suffix)
          decoder_stage += 1
        return decoder_features