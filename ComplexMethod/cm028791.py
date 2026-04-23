def __init__(self,
               output_size: List[int],
               num_classes: float,
               image_field_key: str = DEFAULT_IMAGE_FIELD_KEY,
               label_field_key: str = DEFAULT_LABEL_FIELD_KEY,
               decode_jpeg_only: bool = True,
               aug_rand_hflip: bool = True,
               aug_crop: Optional[bool] = True,
               aug_type: Optional[common.Augmentation] = None,
               color_jitter: float = 0.,
               random_erasing: Optional[common.RandomErasing] = None,
               is_multilabel: bool = False,
               dtype: str = 'float32',
               crop_area_range: Optional[Tuple[float, float]] = (0.08, 1.0),
               center_crop_fraction: Optional[
                   float] = preprocess_ops.CENTER_CROP_FRACTION,
               tf_resize_method: str = 'bilinear',
               three_augment: bool = False):
    """Initializes parameters for parsing annotations in the dataset.

    Args:
      output_size: `Tensor` or `list` for [height, width] of output image. The
        output_size should be divided by the largest feature stride 2^max_level.
      num_classes: `float`, number of classes.
      image_field_key: `str`, the key name to encoded image or decoded image
        matrix in tf.Example.
      label_field_key: `str`, the key name to label in tf.Example.
      decode_jpeg_only: `bool`, if True, only JPEG format is decoded, this is
        faster than decoding other types. Default is True.
      aug_rand_hflip: `bool`, if True, augment training with random horizontal
        flip.
      aug_crop: `bool`, if True, perform random cropping during training and
        center crop during validation.
      aug_type: An optional Augmentation object to choose from AutoAugment and
        RandAugment.
      color_jitter: Magnitude of color jitter. If > 0, the value is used to
        generate random scale factor for brightness, contrast and saturation.
        See `preprocess_ops.color_jitter` for more details.
      random_erasing: if not None, augment input image by random erasing. See
        `augment.RandomErasing` for more details.
      is_multilabel: A `bool`, whether or not each example has multiple labels.
      dtype: `str`, cast output image in dtype. It can be 'float32', 'float16',
        or 'bfloat16'.
      crop_area_range: An optional `tuple` of (min_area, max_area) for image
        random crop function to constraint crop operation. The cropped areas
        of the image must contain a fraction of the input image within this
        range. The default area range is (0.08, 1.0).
      https://arxiv.org/abs/2204.07118.
      center_crop_fraction: center_crop_fraction.
      tf_resize_method: A `str`, interpolation method for resizing image.
      three_augment: A bool, whether to apply three augmentations.
    """
    self._output_size = output_size
    self._aug_rand_hflip = aug_rand_hflip
    self._aug_crop = aug_crop
    self._num_classes = num_classes
    self._image_field_key = image_field_key
    if dtype == 'float32':
      self._dtype = tf.float32
    elif dtype == 'float16':
      self._dtype = tf.float16
    elif dtype == 'bfloat16':
      self._dtype = tf.bfloat16
    else:
      raise ValueError('dtype {!r} is not supported!'.format(dtype))
    if aug_type:
      if aug_type.type == 'autoaug':
        self._augmenter = augment.AutoAugment(
            augmentation_name=aug_type.autoaug.augmentation_name,
            cutout_const=aug_type.autoaug.cutout_const,
            translate_const=aug_type.autoaug.translate_const)
      elif aug_type.type == 'randaug':
        self._augmenter = augment.RandAugment(
            num_layers=aug_type.randaug.num_layers,
            magnitude=aug_type.randaug.magnitude,
            cutout_const=aug_type.randaug.cutout_const,
            translate_const=aug_type.randaug.translate_const,
            prob_to_apply=aug_type.randaug.prob_to_apply,
            exclude_ops=aug_type.randaug.exclude_ops)
      else:
        raise ValueError('Augmentation policy {} not supported.'.format(
            aug_type.type))
    else:
      self._augmenter = None
    self._label_field_key = label_field_key
    self._color_jitter = color_jitter
    if random_erasing:
      self._random_erasing = augment.RandomErasing(
          probability=random_erasing.probability,
          min_area=random_erasing.min_area,
          max_area=random_erasing.max_area,
          min_aspect=random_erasing.min_aspect,
          max_aspect=random_erasing.max_aspect,
          min_count=random_erasing.min_count,
          max_count=random_erasing.max_count,
          trials=random_erasing.trials)
    else:
      self._random_erasing = None
    self._is_multilabel = is_multilabel
    self._decode_jpeg_only = decode_jpeg_only
    self._crop_area_range = crop_area_range
    self._center_crop_fraction = center_crop_fraction
    self._tf_resize_method = tf_resize_method
    self._three_augment = three_augment