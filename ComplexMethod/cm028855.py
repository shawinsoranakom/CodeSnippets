def create_tf_example(image,
                      image_dirs,
                      panoptic_masks_dir=None,
                      bbox_annotations=None,
                      id_to_name_map=None,
                      caption_annotations=None,
                      panoptic_annotation=None,
                      is_category_thing=None,
                      include_panoptic_masks=False,
                      include_masks=False):
  """Converts image and annotations to a tf.Example proto.

  Args:
    image: dict with keys: [u'license', u'file_name', u'coco_url', u'height',
      u'width', u'date_captured', u'flickr_url', u'id']
    image_dirs: list of directories containing the image files.
    panoptic_masks_dir: `str` of the panoptic masks directory.
    bbox_annotations:
      list of dicts with keys: [u'segmentation', u'area', u'iscrowd',
        u'image_id', u'bbox', u'category_id', u'id'] Notice that bounding box
        coordinates in the official COCO dataset are given as [x, y, width,
        height] tuples using absolute coordinates where x, y represent the
        top-left (0-indexed) corner.  This function converts to the format
        expected by the Tensorflow Object Detection API (which is which is
        [ymin, xmin, ymax, xmax] with coordinates normalized relative to image
        size).
    id_to_name_map: a dict mapping category IDs to string names.
    caption_annotations:
      list of dict with keys: [u'id', u'image_id', u'str'].
    panoptic_annotation: dict with keys: [u'image_id', u'file_name',
      u'segments_info']. Where the value for segments_info is a list of dicts,
      with each dict containing information for a single segment in the mask.
    is_category_thing: `bool`, whether it is a category thing.
    include_panoptic_masks: `bool`, whether to include panoptic masks.
    include_masks: Whether to include instance segmentations masks
      (PNG encoded) in the result. default: False.

  Returns:
    example: The converted tf.Example
    num_annotations_skipped: Number of (invalid) annotations that were ignored.

  Raises:
    ValueError: if the image pointed to by data['filename'] is not a valid JPEG,
      does not exist, or is not unique across image directories.
  """
  image_height = image['height']
  image_width = image['width']
  filename = image['file_name']
  image_id = image['id']

  if len(image_dirs) > 1:
    full_paths = [os.path.join(image_dir, filename) for image_dir in image_dirs]
    full_existing_paths = [p for p in full_paths if tf.io.gfile.exists(p)]
    if not full_existing_paths:
      raise ValueError(
          '{} does not exist across image directories.'.format(filename))
    if len(full_existing_paths) > 1:
      raise ValueError(
          '{} is not unique across image directories'.format(filename))
    full_path, = full_existing_paths
  # If there is only one image directory, it's not worth checking for existence,
  # since trying to open the file will raise an informative error message if it
  # does not exist.
  else:
    image_dir, = image_dirs
    full_path = os.path.join(image_dir, filename)

  with tf.io.gfile.GFile(full_path, 'rb') as fid:
    encoded_jpg = fid.read()

  feature_dict = tfrecord_lib.image_info_to_feature_dict(
      image_height, image_width, filename, image_id, encoded_jpg, 'jpg')

  num_annotations_skipped = 0
  if bbox_annotations:
    box_feature_dict, num_skipped = bbox_annotations_to_feature_dict(
        bbox_annotations, image_height, image_width, id_to_name_map,
        include_masks)
    num_annotations_skipped += num_skipped
    feature_dict.update(box_feature_dict)

  if caption_annotations:
    encoded_captions = encode_caption_annotations(caption_annotations)
    feature_dict.update(
        {'image/caption': tfrecord_lib.convert_to_feature(encoded_captions)})

  if panoptic_annotation:
    segments_info = panoptic_annotation['segments_info']
    panoptic_mask_filename = os.path.join(
        panoptic_masks_dir,
        panoptic_annotation['file_name'])
    encoded_panoptic_masks = generate_coco_panoptics_masks(
        segments_info, panoptic_mask_filename, include_panoptic_masks,
        is_category_thing)
    feature_dict.update(
        {'image/segmentation/class/encoded': tfrecord_lib.convert_to_feature(
            encoded_panoptic_masks['semantic_segmentation_mask'])})

    if include_panoptic_masks:
      feature_dict.update({
          'image/panoptic/category_mask': tfrecord_lib.convert_to_feature(
              encoded_panoptic_masks['category_mask']),
          'image/panoptic/instance_mask': tfrecord_lib.convert_to_feature(
              encoded_panoptic_masks['instance_mask'])
            })

  example = tf.train.Example(features=tf.train.Features(feature=feature_dict))
  return example, num_annotations_skipped