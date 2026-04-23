def generate_coco_panoptics_masks(segments_info, mask_path,
                                  include_panoptic_masks,
                                  is_category_thing):
  """Creates masks for panoptic segmentation task.

  Args:
    segments_info: a list of dicts, where each dict has keys: [u'id',
      u'category_id', u'area', u'bbox', u'iscrowd'], detailing information for
      each segment in the panoptic mask.
    mask_path: path to the panoptic mask.
    include_panoptic_masks: bool, when set to True, category and instance
      masks are included in the outputs. Set this to True, when using
      the Panoptic Quality evaluator.
    is_category_thing: a dict with category ids as keys and, 0/1 as values to
      represent "stuff" and "things" classes respectively.

  Returns:
    A dict with keys: [u'semantic_segmentation_mask', u'category_mask',
      u'instance_mask']. The dict contains 'category_mask' and 'instance_mask'
      only if `include_panoptic_eval_masks` is set to True.
  """
  rgb_mask = tfrecord_lib.read_image(mask_path)
  r, g, b = np.split(rgb_mask, 3, axis=-1)

  # decode rgb encoded panoptic mask to get segments ids
  # refer https://cocodataset.org/#format-data
  segments_encoded_mask = (r + g * 256 + b * (256**2)).squeeze()

  semantic_segmentation_mask = np.ones_like(
      segments_encoded_mask, dtype=np.uint8) * _VOID_LABEL
  if include_panoptic_masks:
    category_mask = np.ones_like(
        segments_encoded_mask, dtype=np.uint8) * _VOID_LABEL
    instance_mask = np.ones_like(
        segments_encoded_mask, dtype=np.uint8) * _VOID_INSTANCE_ID

  for idx, segment in enumerate(segments_info):
    segment_id = segment['id']
    category_id = segment['category_id']
    is_crowd = segment['iscrowd']
    if FLAGS.panoptic_skip_crowd and is_crowd:
      continue
    if is_category_thing[category_id]:
      encoded_category_id = _THING_CLASS_ID
      instance_id = idx + 1
    else:
      encoded_category_id = category_id - _STUFF_CLASSES_OFFSET
      instance_id = _VOID_INSTANCE_ID

    segment_mask = (segments_encoded_mask == segment_id)
    semantic_segmentation_mask[segment_mask] = encoded_category_id

    if include_panoptic_masks:
      category_mask[segment_mask] = category_id
      instance_mask[segment_mask] = instance_id

  outputs = {
      'semantic_segmentation_mask': tfrecord_lib.encode_mask_as_png(
          semantic_segmentation_mask)
      }

  if include_panoptic_masks:
    outputs.update({
        'category_mask': tfrecord_lib.encode_mask_as_png(category_mask),
        'instance_mask': tfrecord_lib.encode_mask_as_png(instance_mask)
        })
  return outputs