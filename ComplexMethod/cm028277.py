def create_tf_example(image,
                      annotations_list,
                      image_dir,
                      category_index,
                      include_masks=False,
                      keypoint_annotations_dict=None,
                      densepose_annotations_dict=None,
                      remove_non_person_annotations=False,
                      remove_non_person_images=False):
  """Converts image and annotations to a tf.Example proto.

  Args:
    image: dict with keys: [u'license', u'file_name', u'coco_url', u'height',
      u'width', u'date_captured', u'flickr_url', u'id']
    annotations_list:
      list of dicts with keys: [u'segmentation', u'area', u'iscrowd',
        u'image_id', u'bbox', u'category_id', u'id'] Notice that bounding box
        coordinates in the official COCO dataset are given as [x, y, width,
        height] tuples using absolute coordinates where x, y represent the
        top-left (0-indexed) corner.  This function converts to the format
        expected by the Tensorflow Object Detection API (which is which is
        [ymin, xmin, ymax, xmax] with coordinates normalized relative to image
        size).
    image_dir: directory containing the image files.
    category_index: a dict containing COCO category information keyed by the
      'id' field of each category.  See the label_map_util.create_category_index
      function.
    include_masks: Whether to include instance segmentations masks
      (PNG encoded) in the result. default: False.
    keypoint_annotations_dict: A dictionary that maps from annotation_id to a
      dictionary with keys: [u'keypoints', u'num_keypoints'] represeting the
      keypoint information for this person object annotation. If None, then
      no keypoint annotations will be populated.
    densepose_annotations_dict: A dictionary that maps from annotation_id to a
      dictionary with keys: [u'dp_I', u'dp_x', u'dp_y', 'dp_U', 'dp_V']
      representing part surface coordinates. For more information see
      http://densepose.org/.
    remove_non_person_annotations: Whether to remove any annotations that are
      not the "person" class.
    remove_non_person_images: Whether to remove any images that do not contain
      at least one "person" annotation.

  Returns:
    key: SHA256 hash of the image.
    example: The converted tf.Example
    num_annotations_skipped: Number of (invalid) annotations that were ignored.
    num_keypoint_annotation_skipped: Number of keypoint annotations that were
      skipped.
    num_densepose_annotation_skipped: Number of DensePose annotations that were
      skipped.

  Raises:
    ValueError: if the image pointed to by data['filename'] is not a valid JPEG
  """
  image_height = image['height']
  image_width = image['width']
  filename = image['file_name']
  image_id = image['id']

  full_path = os.path.join(image_dir, filename)
  with tf.gfile.GFile(full_path, 'rb') as fid:
    encoded_jpg = fid.read()
  encoded_jpg_io = io.BytesIO(encoded_jpg)
  image = PIL.Image.open(encoded_jpg_io)
  key = hashlib.sha256(encoded_jpg).hexdigest()

  xmin = []
  xmax = []
  ymin = []
  ymax = []
  is_crowd = []
  category_names = []
  category_ids = []
  area = []
  encoded_mask_png = []
  keypoints_x = []
  keypoints_y = []
  keypoints_visibility = []
  keypoints_name = []
  num_keypoints = []
  include_keypoint = keypoint_annotations_dict is not None
  num_annotations_skipped = 0
  num_keypoint_annotation_used = 0
  num_keypoint_annotation_skipped = 0
  dp_part_index = []
  dp_x = []
  dp_y = []
  dp_u = []
  dp_v = []
  dp_num_points = []
  densepose_keys = ['dp_I', 'dp_U', 'dp_V', 'dp_x', 'dp_y', 'bbox']
  include_densepose = densepose_annotations_dict is not None
  num_densepose_annotation_used = 0
  num_densepose_annotation_skipped = 0
  for object_annotations in annotations_list:
    (x, y, width, height) = tuple(object_annotations['bbox'])
    if width <= 0 or height <= 0:
      num_annotations_skipped += 1
      continue
    if x + width > image_width or y + height > image_height:
      num_annotations_skipped += 1
      continue
    category_id = int(object_annotations['category_id'])
    category_name = category_index[category_id]['name'].encode('utf8')
    if remove_non_person_annotations and category_name != b'person':
      num_annotations_skipped += 1
      continue
    xmin.append(float(x) / image_width)
    xmax.append(float(x + width) / image_width)
    ymin.append(float(y) / image_height)
    ymax.append(float(y + height) / image_height)
    is_crowd.append(object_annotations['iscrowd'])
    category_ids.append(category_id)
    category_names.append(category_name)
    area.append(object_annotations['area'])

    if include_masks:
      run_len_encoding = mask.frPyObjects(object_annotations['segmentation'],
                                          image_height, image_width)
      binary_mask = mask.decode(run_len_encoding)
      if not object_annotations['iscrowd']:
        binary_mask = np.amax(binary_mask, axis=2)
      pil_image = PIL.Image.fromarray(binary_mask)
      output_io = io.BytesIO()
      pil_image.save(output_io, format='PNG')
      encoded_mask_png.append(output_io.getvalue())

    if include_keypoint:
      annotation_id = object_annotations['id']
      if annotation_id in keypoint_annotations_dict:
        num_keypoint_annotation_used += 1
        keypoint_annotations = keypoint_annotations_dict[annotation_id]
        keypoints = keypoint_annotations['keypoints']
        num_kpts = keypoint_annotations['num_keypoints']
        keypoints_x_abs = keypoints[::3]
        keypoints_x.extend(
            [float(x_abs) / image_width for x_abs in keypoints_x_abs])
        keypoints_y_abs = keypoints[1::3]
        keypoints_y.extend(
            [float(y_abs) / image_height for y_abs in keypoints_y_abs])
        keypoints_visibility.extend(keypoints[2::3])
        keypoints_name.extend(_COCO_KEYPOINT_NAMES)
        num_keypoints.append(num_kpts)
      else:
        keypoints_x.extend([0.0] * len(_COCO_KEYPOINT_NAMES))
        keypoints_y.extend([0.0] * len(_COCO_KEYPOINT_NAMES))
        keypoints_visibility.extend([0] * len(_COCO_KEYPOINT_NAMES))
        keypoints_name.extend(_COCO_KEYPOINT_NAMES)
        num_keypoints.append(0)

    if include_densepose:
      annotation_id = object_annotations['id']
      if (annotation_id in densepose_annotations_dict and
          all(key in densepose_annotations_dict[annotation_id]
              for key in densepose_keys)):
        dp_annotations = densepose_annotations_dict[annotation_id]
        num_densepose_annotation_used += 1
        dp_num_points.append(len(dp_annotations['dp_I']))
        dp_part_index.extend([int(i - _DP_PART_ID_OFFSET)
                              for i in dp_annotations['dp_I']])
        # DensePose surface coordinates are defined on a [256, 256] grid
        # relative to each instance box (i.e. absolute coordinates in range
        # [0., 256.]). The following converts the coordinates
        # so that they are expressed in normalized image coordinates.
        dp_x_box_rel = [
            clip_to_unit(val / 256.) for val in dp_annotations['dp_x']]
        dp_x_norm = [(float(x) + x_box_rel * width) / image_width
                     for x_box_rel in dp_x_box_rel]
        dp_y_box_rel = [
            clip_to_unit(val / 256.) for val in dp_annotations['dp_y']]
        dp_y_norm = [(float(y) + y_box_rel * height) / image_height
                     for y_box_rel in dp_y_box_rel]
        dp_x.extend(dp_x_norm)
        dp_y.extend(dp_y_norm)
        dp_u.extend(dp_annotations['dp_U'])
        dp_v.extend(dp_annotations['dp_V'])
      else:
        dp_num_points.append(0)

  if (remove_non_person_images and
      not any(name == b'person' for name in category_names)):
    return (key, None, num_annotations_skipped,
            num_keypoint_annotation_skipped, num_densepose_annotation_skipped)
  feature_dict = {
      'image/height':
          dataset_util.int64_feature(image_height),
      'image/width':
          dataset_util.int64_feature(image_width),
      'image/filename':
          dataset_util.bytes_feature(filename.encode('utf8')),
      'image/source_id':
          dataset_util.bytes_feature(str(image_id).encode('utf8')),
      'image/key/sha256':
          dataset_util.bytes_feature(key.encode('utf8')),
      'image/encoded':
          dataset_util.bytes_feature(encoded_jpg),
      'image/format':
          dataset_util.bytes_feature('jpeg'.encode('utf8')),
      'image/object/bbox/xmin':
          dataset_util.float_list_feature(xmin),
      'image/object/bbox/xmax':
          dataset_util.float_list_feature(xmax),
      'image/object/bbox/ymin':
          dataset_util.float_list_feature(ymin),
      'image/object/bbox/ymax':
          dataset_util.float_list_feature(ymax),
      'image/object/class/text':
          dataset_util.bytes_list_feature(category_names),
      'image/object/is_crowd':
          dataset_util.int64_list_feature(is_crowd),
      'image/object/area':
          dataset_util.float_list_feature(area),
  }
  if include_masks:
    feature_dict['image/object/mask'] = (
        dataset_util.bytes_list_feature(encoded_mask_png))
  if include_keypoint:
    feature_dict['image/object/keypoint/x'] = (
        dataset_util.float_list_feature(keypoints_x))
    feature_dict['image/object/keypoint/y'] = (
        dataset_util.float_list_feature(keypoints_y))
    feature_dict['image/object/keypoint/num'] = (
        dataset_util.int64_list_feature(num_keypoints))
    feature_dict['image/object/keypoint/visibility'] = (
        dataset_util.int64_list_feature(keypoints_visibility))
    feature_dict['image/object/keypoint/text'] = (
        dataset_util.bytes_list_feature(keypoints_name))
    num_keypoint_annotation_skipped = (
        len(keypoint_annotations_dict) - num_keypoint_annotation_used)
  if include_densepose:
    feature_dict['image/object/densepose/num'] = (
        dataset_util.int64_list_feature(dp_num_points))
    feature_dict['image/object/densepose/part_index'] = (
        dataset_util.int64_list_feature(dp_part_index))
    feature_dict['image/object/densepose/x'] = (
        dataset_util.float_list_feature(dp_x))
    feature_dict['image/object/densepose/y'] = (
        dataset_util.float_list_feature(dp_y))
    feature_dict['image/object/densepose/u'] = (
        dataset_util.float_list_feature(dp_u))
    feature_dict['image/object/densepose/v'] = (
        dataset_util.float_list_feature(dp_v))
    num_densepose_annotation_skipped = (
        len(densepose_annotations_dict) - num_densepose_annotation_used)

  example = tf.train.Example(features=tf.train.Features(feature=feature_dict))
  return (key, example, num_annotations_skipped,
          num_keypoint_annotation_skipped, num_densepose_annotation_skipped)