def add_softmax_cross_entropy_loss_for_each_scale(scales_to_logits,
                                                  labels,
                                                  num_classes,
                                                  ignore_label,
                                                  loss_weight=1.0,
                                                  upsample_logits=True,
                                                  hard_example_mining_step=0,
                                                  top_k_percent_pixels=1.0,
                                                  gt_is_matting_map=False,
                                                  scope=None):
  """Adds softmax cross entropy loss for logits of each scale.

  Args:
    scales_to_logits: A map from logits names for different scales to logits.
      The logits have shape [batch, logits_height, logits_width, num_classes].
    labels: Groundtruth labels with shape [batch, image_height, image_width, 1].
    num_classes: Integer, number of target classes.
    ignore_label: Integer, label to ignore.
    loss_weight: A float or a list of loss weights. If it is a float, it means
      all the labels have the same weight. If it is a list of weights, then each
      element in the list represents the weight for the label of its index, for
      example, loss_weight = [0.1, 0.5] means the weight for label 0 is 0.1 and
      the weight for label 1 is 0.5.
    upsample_logits: Boolean, upsample logits or not.
    hard_example_mining_step: An integer, the training step in which the hard
      exampling mining kicks off. Note that we gradually reduce the mining
      percent to the top_k_percent_pixels. For example, if
      hard_example_mining_step = 100K and top_k_percent_pixels = 0.25, then
      mining percent will gradually reduce from 100% to 25% until 100K steps
      after which we only mine top 25% pixels.
    top_k_percent_pixels: A float, the value lies in [0.0, 1.0]. When its value
      < 1.0, only compute the loss for the top k percent pixels (e.g., the top
      20% pixels). This is useful for hard pixel mining.
    gt_is_matting_map: If true, the groundtruth is a matting map of confidence
      score. If false, the groundtruth is an integer valued class mask.
    scope: String, the scope for the loss.

  Raises:
    ValueError: Label or logits is None, or groundtruth is matting map while
      label is not floating value.
  """
  if labels is None:
    raise ValueError('No label for softmax cross entropy loss.')

  # If input groundtruth is a matting map of confidence, check if the input
  # labels are floating point values.
  if gt_is_matting_map and not labels.dtype.is_floating:
    raise ValueError('Labels must be floats if groundtruth is a matting map.')

  for scale, logits in six.iteritems(scales_to_logits):
    loss_scope = None
    if scope:
      loss_scope = '%s_%s' % (scope, scale)

    if upsample_logits:
      # Label is not downsampled, and instead we upsample logits.
      logits = tf.image.resize_bilinear(
          logits,
          preprocess_utils.resolve_shape(labels, 4)[1:3],
          align_corners=True)
      scaled_labels = labels
    else:
      # Label is downsampled to the same size as logits.
      # When gt_is_matting_map = true, label downsampling with nearest neighbor
      # method may introduce artifacts. However, to avoid ignore_label from
      # being interpolated with other labels, we still perform nearest neighbor
      # interpolation.
      # TODO(huizhongc): Change to bilinear interpolation by processing padded
      # and non-padded label separately.
      if gt_is_matting_map:
        tf.logging.warning(
            'Label downsampling with nearest neighbor may introduce artifacts.')

      scaled_labels = tf.image.resize_nearest_neighbor(
          labels,
          preprocess_utils.resolve_shape(logits, 4)[1:3],
          align_corners=True)

    scaled_labels = tf.reshape(scaled_labels, shape=[-1])
    weights = utils.get_label_weight_mask(
        scaled_labels, ignore_label, num_classes, label_weights=loss_weight)
    # Dimension of keep_mask is equal to the total number of pixels.
    keep_mask = tf.cast(
        tf.not_equal(scaled_labels, ignore_label), dtype=tf.float32)

    train_labels = None
    logits = tf.reshape(logits, shape=[-1, num_classes])

    if gt_is_matting_map:
      # When the groundtruth is integer label mask, we can assign class
      # dependent label weights to the loss. When the groundtruth is image
      # matting confidence, we do not apply class-dependent label weight (i.e.,
      # label_weight = 1.0).
      if loss_weight != 1.0:
        raise ValueError(
            'loss_weight must equal to 1 if groundtruth is matting map.')

      # Assign label value 0 to ignore pixels. The exact label value of ignore
      # pixel does not matter, because those ignore_value pixel losses will be
      # multiplied to 0 weight.
      train_labels = scaled_labels * keep_mask

      train_labels = tf.expand_dims(train_labels, 1)
      train_labels = tf.concat([1 - train_labels, train_labels], axis=1)
    else:
      train_labels = tf.one_hot(
          scaled_labels, num_classes, on_value=1.0, off_value=0.0)

    default_loss_scope = ('softmax_all_pixel_loss'
                          if top_k_percent_pixels == 1.0 else
                          'softmax_hard_example_mining')
    with tf.name_scope(loss_scope, default_loss_scope,
                       [logits, train_labels, weights]):
      # Compute the loss for all pixels.
      pixel_losses = tf.nn.softmax_cross_entropy_with_logits_v2(
          labels=tf.stop_gradient(
              train_labels, name='train_labels_stop_gradient'),
          logits=logits,
          name='pixel_losses')
      weighted_pixel_losses = tf.multiply(pixel_losses, weights)

      if top_k_percent_pixels == 1.0:
        total_loss = tf.reduce_sum(weighted_pixel_losses)
        num_present = tf.reduce_sum(keep_mask)
        loss = _div_maybe_zero(total_loss, num_present)
        tf.losses.add_loss(loss)
      else:
        num_pixels = tf.to_float(tf.shape(logits)[0])
        # Compute the top_k_percent pixels based on current training step.
        if hard_example_mining_step == 0:
          # Directly focus on the top_k pixels.
          top_k_pixels = tf.to_int32(top_k_percent_pixels * num_pixels)
        else:
          # Gradually reduce the mining percent to top_k_percent_pixels.
          global_step = tf.to_float(tf.train.get_or_create_global_step())
          ratio = tf.minimum(1.0, global_step / hard_example_mining_step)
          top_k_pixels = tf.to_int32(
              (ratio * top_k_percent_pixels + (1.0 - ratio)) * num_pixels)
        top_k_losses, _ = tf.nn.top_k(weighted_pixel_losses,
                                      k=top_k_pixels,
                                      sorted=True,
                                      name='top_k_percent_pixels')
        total_loss = tf.reduce_sum(top_k_losses)
        num_present = tf.reduce_sum(
            tf.to_float(tf.not_equal(top_k_losses, 0.0)))
        loss = _div_maybe_zero(total_loss, num_present)
        tf.losses.add_loss(loss)