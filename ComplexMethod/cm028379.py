def __new__(cls,
              outputs_to_num_classes,
              crop_size=None,
              atrous_rates=None,
              output_stride=8,
              preprocessed_images_dtype=tf.float32):
    """Constructor to set default values.

    Args:
      outputs_to_num_classes: A dictionary from output type to the number of
        classes. For example, for the task of semantic segmentation with 21
        semantic classes, we would have outputs_to_num_classes['semantic'] = 21.
      crop_size: A tuple [crop_height, crop_width].
      atrous_rates: A list of atrous convolution rates for ASPP.
      output_stride: The ratio of input to output spatial resolution.
      preprocessed_images_dtype: The type after the preprocessing function.

    Returns:
      A new ModelOptions instance.
    """
    dense_prediction_cell_config = None
    if FLAGS.dense_prediction_cell_json:
      with tf.gfile.Open(FLAGS.dense_prediction_cell_json, 'r') as f:
        dense_prediction_cell_config = json.load(f)
    decoder_output_stride = None
    if FLAGS.decoder_output_stride:
      decoder_output_stride = [
          int(x) for x in FLAGS.decoder_output_stride]
      if sorted(decoder_output_stride, reverse=True) != decoder_output_stride:
        raise ValueError('Decoder output stride need to be sorted in the '
                         'descending order.')
    image_pooling_crop_size = None
    if FLAGS.image_pooling_crop_size:
      image_pooling_crop_size = [int(x) for x in FLAGS.image_pooling_crop_size]
    image_pooling_stride = [1, 1]
    if FLAGS.image_pooling_stride:
      image_pooling_stride = [int(x) for x in FLAGS.image_pooling_stride]
    label_weights = FLAGS.label_weights
    if label_weights is None:
      label_weights = 1.0
    nas_architecture_options = {
        'nas_stem_output_num_conv_filters': (
            FLAGS.nas_stem_output_num_conv_filters),
        'nas_use_classification_head': FLAGS.nas_use_classification_head,
        'nas_remove_os32_stride': FLAGS.nas_remove_os32_stride,
    }
    return super(ModelOptions, cls).__new__(
        cls, outputs_to_num_classes, crop_size, atrous_rates, output_stride,
        preprocessed_images_dtype,
        FLAGS.merge_method,
        FLAGS.add_image_level_feature,
        image_pooling_crop_size,
        image_pooling_stride,
        FLAGS.aspp_with_batch_norm,
        FLAGS.aspp_with_separable_conv,
        FLAGS.multi_grid,
        decoder_output_stride,
        FLAGS.decoder_use_separable_conv,
        FLAGS.logits_kernel_size,
        FLAGS.model_variant,
        FLAGS.depth_multiplier,
        FLAGS.divisible_by,
        FLAGS.prediction_with_upsampled_logits,
        dense_prediction_cell_config,
        nas_architecture_options,
        FLAGS.use_bounded_activation,
        FLAGS.aspp_with_concat_projection,
        FLAGS.aspp_with_squeeze_and_excitation,
        FLAGS.aspp_convs_filters,
        FLAGS.decoder_use_sum_merge,
        FLAGS.decoder_filters,
        FLAGS.decoder_output_is_logits,
        FLAGS.image_se_uses_qsigmoid,
        label_weights,
        'None',
        FLAGS.batch_norm_decay)