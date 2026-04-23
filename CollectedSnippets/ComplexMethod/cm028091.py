def ExtractorFn(image, resize_factor=1.0):
    """Receives an image and returns DELF global and/or local features.

    If image is too small, returns empty features.

    Args:
      image: Uint8 array with shape (height, width, 3) containing the RGB image.
      resize_factor: Optional float resize factor for the input image. If given,
        the maximum and minimum allowed image sizes in the config are scaled by
        this factor.

    Returns:
      extracted_features: A dict containing the extracted global descriptors
        (key 'global_descriptor' mapping to a [D] float array), and/or local
        features (key 'local_features' mapping to a dict with keys 'locations',
        'descriptors', 'scales', 'attention').
    """
    resized_image, scale_factors = utils.ResizeImage(
        image, config, resize_factor=resize_factor)

    # If the image is too small, returns empty features.
    if resized_image.shape[0] < _MIN_HEIGHT or resized_image.shape[
        1] < _MIN_WIDTH:
      extracted_features = {'global_descriptor': np.array([])}
      if config.use_local_features:
        extracted_features.update({
            'local_features': {
                'locations': np.array([]),
                'descriptors': np.array([]),
                'scales': np.array([]),
                'attention': np.array([]),
            }
        })
      return extracted_features

    # Input tensors.
    image_tensor = tf.convert_to_tensor(resized_image)

    # Extracted features.
    extracted_features = {}
    output = None

    if hasattr(config, 'is_tf2_exported') and config.is_tf2_exported:
      predict = model.signatures['serving_default']
      if config.use_local_features and config.use_global_features:
        output_dict = predict(
            input_image=image_tensor,
            input_scales=image_scales_tensor,
            input_max_feature_num=max_feature_num_tensor,
            input_abs_thres=score_threshold_tensor,
            input_global_scales_ind=global_scales_ind_tensor)
        output = [
            output_dict['boxes'], output_dict['features'],
            output_dict['scales'], output_dict['scores'],
            output_dict['global_descriptors']
        ]
      elif config.use_local_features:
        output_dict = predict(
            input_image=image_tensor,
            input_scales=image_scales_tensor,
            input_max_feature_num=max_feature_num_tensor,
            input_abs_thres=score_threshold_tensor)
        output = [
            output_dict['boxes'], output_dict['features'],
            output_dict['scales'], output_dict['scores']
        ]
      else:
        output_dict = predict(
            input_image=image_tensor,
            input_scales=image_scales_tensor,
            input_global_scales_ind=global_scales_ind_tensor)
        output = [output_dict['global_descriptors']]
    else:
      if config.use_local_features and config.use_global_features:
        output = model(image_tensor, image_scales_tensor,
                       score_threshold_tensor, max_feature_num_tensor,
                       global_scales_ind_tensor)
      elif config.use_local_features:
        output = model(image_tensor, image_scales_tensor,
                       score_threshold_tensor, max_feature_num_tensor)
      else:
        output = model(image_tensor, image_scales_tensor,
                       global_scales_ind_tensor)

    # Post-process extracted features: normalize, PCA (optional), pooling.
    if config.use_global_features:
      raw_global_descriptors = output[-1]
      global_descriptors_per_scale = feature_extractor.PostProcessDescriptors(
          raw_global_descriptors, config.delf_global_config.use_pca,
          global_pca_parameters)
      unnormalized_global_descriptor = tf.reduce_sum(
          global_descriptors_per_scale, axis=0, name='sum_pooling')
      global_descriptor = tf.nn.l2_normalize(
          unnormalized_global_descriptor, axis=0, name='final_l2_normalization')
      extracted_features.update({
          'global_descriptor': global_descriptor.numpy(),
      })

    if config.use_local_features:
      boxes = output[0]
      raw_local_descriptors = output[1]
      feature_scales = output[2]
      attention_with_extra_dim = output[3]

      attention = tf.reshape(attention_with_extra_dim,
                             [tf.shape(attention_with_extra_dim)[0]])
      locations, local_descriptors = (
          feature_extractor.DelfFeaturePostProcessing(
              boxes, raw_local_descriptors, config.delf_local_config.use_pca,
              local_pca_parameters))
      if not config.delf_local_config.use_resized_coordinates:
        locations /= scale_factors

      extracted_features.update({
          'local_features': {
              'locations': locations.numpy(),
              'descriptors': local_descriptors.numpy(),
              'scales': feature_scales.numpy(),
              'attention': attention.numpy(),
          }
      })

    return extracted_features