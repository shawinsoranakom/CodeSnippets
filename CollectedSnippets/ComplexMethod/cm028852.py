def add_encoded_image_feature(
      self,
      encoded_image: bytes,
      image_format: Optional[str] = None,
      height: Optional[int] = None,
      width: Optional[int] = None,
      num_channels: Optional[int] = None,
      image_source_id: Optional[bytes] = None,
      feature_prefix: Optional[str] = None,
      label: Optional[Union[int, Sequence[int]]] = None) -> 'TfExampleBuilder':
    """Adds encoded image features to the example.

    See `tf_example_feature_key.EncodedImageFeatureKey` for list of feature keys
    that will be added to the example.

    Image format, height, width, and channels are inferred from the encoded
    image bytes if any of them is not provided. Hashed image will be used if
    pre-generated source ID is not provided.

    Example usages:
      >>> example_builder = TfExampleBuilder()
      * For adding RGB image feature:
      >>> example_builder.add_encoded_image_feature(image_bytes)
      * For adding RGB image feature with pre-generated source ID:
      >>> example_builder.add_encoded_image_feature(
              image_bytes, image_source_id=image_source_id)
      * For adding single-channel depth image feature:
      >>> example_builder.add_encoded_image_feature(
              image_bytes, feature_prefix='depth')

    Args:
      encoded_image: Encoded image string.
      image_format: Image format string.
      height: Number of rows.
      width: Number of columns.
      num_channels: Number of channels.
      image_source_id: Unique string ID to identify the image.
      feature_prefix: Feature prefix for image features.
      label: the label or a list of labels for the image.

    Returns:
      The builder object for subsequent method calls.
    """
    if image_format == 'RAW':
      if not (height and width and num_channels):
        raise ValueError('For raw image feature, height, width and '
                         'num_channels fields are required.')
    if not all((height, width, num_channels, image_format)):
      (height, width, num_channels, image_format) = (
          image_utils.decode_image_metadata(encoded_image))
    else:
      image_format = image_utils.validate_image_format(image_format)

    feature_key = tf_example_feature_key.EncodedImageFeatureKey(feature_prefix)

    # If source ID is not provided, we use hashed encoded image as the source
    # ID. Note that we only keep 24 bits to be consistent with the Model Garden
    # requirement, which will transform the source ID into float32.
    if not image_source_id:
      hashed_image = int(hashlib.blake2s(encoded_image).hexdigest(), 16)
      image_source_id = _to_bytes(str(hashed_image % ((1 << 24) + 1)))

    if label is not None:
      self.add_ints_feature(feature_key.label, label)

    return (
        self.add_bytes_feature(feature_key.encoded, encoded_image)
        .add_bytes_feature(feature_key.format, image_format)
        .add_ints_feature(feature_key.height, [height])
        .add_ints_feature(feature_key.width, [width])
        .add_ints_feature(feature_key.num_channels, num_channels)
        .add_bytes_feature(feature_key.source_id, image_source_id))