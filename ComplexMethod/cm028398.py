def build_cell(self,
                 features,
                 output_stride=16,
                 crop_size=None,
                 image_pooling_crop_size=None,
                 weight_decay=0.00004,
                 reuse=None,
                 is_training=False,
                 fine_tune_batch_norm=False,
                 scope=None):
    """Builds the dense prediction cell based on the config.

    Args:
      features: Input feature map of size [batch, height, width, channels].
      output_stride: Int, output stride at which the features were extracted.
      crop_size: A list [crop_height, crop_width], determining the input
        features resolution.
      image_pooling_crop_size: A list of two integers, [crop_height, crop_width]
        specifying the crop size for image pooling operations. Note that we
        decouple whole patch crop_size and image_pooling_crop_size as one could
        perform the image_pooling with different crop sizes.
      weight_decay: Float, the weight decay for model variables.
      reuse: Reuse the model variables or not.
      is_training: Boolean, is training or not.
      fine_tune_batch_norm: Boolean, fine-tuning batch norm parameters or not.
      scope: Optional string, specifying the variable scope.

    Returns:
      Features after passing through the constructed dense prediction cell with
        shape = [batch, height, width, channels] where channels are determined
        by `reduction_size` returned by dense_prediction_cell_hparams().

    Raises:
      ValueError: Use Convolution with kernel size not equal to 1x1 or 3x3 or
        the operation is not recognized.
    """
    batch_norm_params = {
        'is_training': is_training and fine_tune_batch_norm,
        'decay': 0.9997,
        'epsilon': 1e-5,
        'scale': True,
    }
    hparams = self.hparams
    with slim.arg_scope(
        [slim.conv2d, slim.separable_conv2d],
        weights_regularizer=slim.l2_regularizer(weight_decay),
        activation_fn=tf.nn.relu,
        normalizer_fn=slim.batch_norm,
        padding='SAME',
        stride=1,
        reuse=reuse):
      with slim.arg_scope([slim.batch_norm], **batch_norm_params):
        with tf.variable_scope(scope, _META_ARCHITECTURE_SCOPE, [features]):
          depth = hparams['reduction_size']
          branch_logits = []
          for i, current_config in enumerate(self.config):
            scope = 'branch%d' % i
            current_config = self._parse_operation(
                config=current_config,
                crop_size=crop_size,
                output_stride=output_stride,
                image_pooling_crop_size=image_pooling_crop_size)
            tf.logging.info(current_config)
            if current_config[_INPUT] < 0:
              operation_input = features
            else:
              operation_input = branch_logits[current_config[_INPUT]]
            if current_config[_OP] == _CONV:
              if current_config[_KERNEL] == [1, 1] or current_config[
                  _KERNEL] == 1:
                branch_logits.append(
                    slim.conv2d(operation_input, depth, 1, scope=scope))
              else:
                conv_rate = [r * hparams['conv_rate_multiplier']
                             for r in current_config[_RATE]]
                branch_logits.append(
                    utils.split_separable_conv2d(
                        operation_input,
                        filters=depth,
                        kernel_size=current_config[_KERNEL],
                        rate=conv_rate,
                        weight_decay=weight_decay,
                        scope=scope))
            elif current_config[_OP] == _PYRAMID_POOLING:
              pooled_features = slim.avg_pool2d(
                  operation_input,
                  kernel_size=current_config[_KERNEL],
                  stride=[1, 1],
                  padding='VALID')
              pooled_features = slim.conv2d(
                  pooled_features,
                  depth,
                  1,
                  scope=scope)
              pooled_features = tf.image.resize_bilinear(
                  pooled_features,
                  current_config[_TARGET_SIZE],
                  align_corners=True)
              # Set shape for resize_height/resize_width if they are not Tensor.
              resize_height = current_config[_TARGET_SIZE][0]
              resize_width = current_config[_TARGET_SIZE][1]
              if isinstance(resize_height, tf.Tensor):
                resize_height = None
              if isinstance(resize_width, tf.Tensor):
                resize_width = None
              pooled_features.set_shape(
                  [None, resize_height, resize_width, depth])
              branch_logits.append(pooled_features)
            else:
              raise ValueError('Unrecognized operation.')
          # Merge branch logits.
          concat_logits = tf.concat(branch_logits, 3)
          if self.hparams['dropout_on_concat_features']:
            concat_logits = slim.dropout(
                concat_logits,
                keep_prob=self.hparams['dropout_keep_prob'],
                is_training=is_training,
                scope=_CONCAT_PROJECTION_SCOPE + '_dropout')
          concat_logits = slim.conv2d(concat_logits,
                                      self.hparams['concat_channels'],
                                      1,
                                      scope=_CONCAT_PROJECTION_SCOPE)
          if self.hparams['dropout_on_projection_features']:
            concat_logits = slim.dropout(
                concat_logits,
                keep_prob=self.hparams['dropout_keep_prob'],
                is_training=is_training,
                scope=_CONCAT_PROJECTION_SCOPE + '_dropout')
          return concat_logits