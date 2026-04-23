def process(self, image_id):
    """Builds a tf.Example given an image id.

    Args:
      image_id: the image id of the associated image

    Returns:
      List of tf.Examples.
    """

    image = self._image_dict[image_id]
    annotations = self._annotation_dict[image_id]
    image_height = image['height']
    image_width = image['width']
    filename = image['file_name']
    image_id = image['id']
    image_location_id = image['location']

    image_datetime = str(image['date_captured'])

    image_sequence_id = str(image['seq_id'])
    image_sequence_num_frames = int(image['seq_num_frames'])
    image_sequence_frame_num = int(image['frame_num'])

    full_path = os.path.join(self._image_directory, filename)

    try:
      # Ensure the image exists and is not corrupted
      with tf.io.gfile.GFile(full_path, 'rb') as fid:
        encoded_jpg = fid.read()
      encoded_jpg_io = io.BytesIO(encoded_jpg)
      image = PIL.Image.open(encoded_jpg_io)
      image = tf.io.decode_jpeg(encoded_jpg, channels=3)
    except Exception:  # pylint: disable=broad-except
      # The image file is missing or corrupt
      return []

    key = hashlib.sha256(encoded_jpg).hexdigest()
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
        'image/location':
            dataset_util.bytes_feature(str(image_location_id).encode('utf8')),
        'image/seq_num_frames':
            dataset_util.int64_feature(image_sequence_num_frames),
        'image/seq_frame_num':
            dataset_util.int64_feature(image_sequence_frame_num),
        'image/seq_id':
            dataset_util.bytes_feature(image_sequence_id.encode('utf8')),
        'image/date_captured':
            dataset_util.bytes_feature(image_datetime.encode('utf8'))
    }

    num_annotations_skipped = 0
    if annotations:
      xmin = []
      xmax = []
      ymin = []
      ymax = []
      category_names = []
      category_ids = []
      area = []

      for object_annotations in annotations:
        if 'bbox' in object_annotations and self._keep_bboxes:
          (x, y, width, height) = tuple(object_annotations['bbox'])
          if width <= 0 or height <= 0:
            num_annotations_skipped += 1
            continue
          if x + width > image_width or y + height > image_height:
            num_annotations_skipped += 1
            continue
          xmin.append(float(x) / image_width)
          xmax.append(float(x + width) / image_width)
          ymin.append(float(y) / image_height)
          ymax.append(float(y + height) / image_height)
          if 'area' in object_annotations:
            area.append(object_annotations['area'])
          else:
            # approximate area using l*w/2
            area.append(width*height/2.0)

        category_id = int(object_annotations['category_id'])
        category_ids.append(category_id)
        category_names.append(
            self._category_dict[category_id]['name'].encode('utf8'))

      feature_dict.update({
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
          'image/object/class/label':
              dataset_util.int64_list_feature(category_ids),
          'image/object/area':
              dataset_util.float_list_feature(area),
      })

      # For classification, add the first category to image/class/label and
      # image/class/text
      if not category_ids:
        feature_dict.update({
            'image/class/label':
                dataset_util.int64_list_feature([0]),
            'image/class/text':
                dataset_util.bytes_list_feature(['empty'.encode('utf8')]),
        })
      else:
        feature_dict.update({
            'image/class/label':
                dataset_util.int64_list_feature([category_ids[0]]),
            'image/class/text':
                dataset_util.bytes_list_feature([category_names[0]]),
        })

    else:
      # Add empty class if there are no annotations
      feature_dict.update({
          'image/class/label':
              dataset_util.int64_list_feature([0]),
          'image/class/text':
              dataset_util.bytes_list_feature(['empty'.encode('utf8')]),
      })

    example = tf.train.Example(features=tf.train.Features(feature=feature_dict))
    self._num_examples_processed.inc(1)

    return [(example)]