def extract_labels(self, frame: dataset_pb2.Frame) -> Sequence[tf.Tensor]:
    """Extract bounding box labels from frame proto.

    Args:
      frame: A frame message in wod dataset.proto.

    Returns:
      labels: A sequence of processed tensors.
    """
    xmin = []
    xmax = []
    ymin = []
    ymax = []
    classes = []
    heading = []
    z = []
    height = []
    difficulty = []

    for label in frame.laser_labels:
      box = label.box

      # Skip boxes if it doesn't contain any lidar points.
      # WARNING: Do not enable this filter when using v.1.0.0 data.
      if label.num_lidar_points_in_box == 0:
        continue

      # Skip boxes if it's type is SIGN.
      if label.type == label_pb2.Label.TYPE_SIGN:
        continue

      # Skip boxes if its z is out of range.
      half_height = box.height * 0.5
      if (box.center_z - half_height < self._z_range[0] or
          box.center_z + half_height > self._z_range[1]):
        continue

      # Get boxes in image coordinate.
      frame_box = np.array([[box.center_x, box.center_y, box.length,
                             box.width]])
      image_box = utils.frame_to_image_boxes(frame_box, self._vehicle_xy,
                                             self._one_over_resolution)
      # Skip empty boxes.
      image_box = utils.clip_boxes(image_box, self._image_height,
                                   self._image_width)[0]
      y0, x0, y1, x1 = image_box
      if np.abs(y0 - y1) < _MIN_BOX_LENGTH or np.abs(x0 - x1) < _MIN_BOX_LENGTH:
        continue

      label_cls = self._adjust_label_type(label)
      level = self._adjust_difficulty_level(label)

      classes.append(label_cls)
      ymin.append(y0)
      xmin.append(x0)
      ymax.append(y1)
      xmax.append(x1)
      heading.append(box.heading)
      z.append(box.center_z)
      height.append(box.height)
      difficulty.append(level)

    classes = tf.convert_to_tensor(classes, dtype=tf.int32)
    ymin = tf.convert_to_tensor(ymin, dtype=tf.float32)
    xmin = tf.convert_to_tensor(xmin, dtype=tf.float32)
    ymax = tf.convert_to_tensor(ymax, dtype=tf.float32)
    xmax = tf.convert_to_tensor(xmax, dtype=tf.float32)
    heading = tf.convert_to_tensor(heading, dtype=tf.float32)
    z = tf.convert_to_tensor(z, dtype=tf.float32)
    height = tf.convert_to_tensor(height, dtype=tf.float32)
    difficulty = tf.convert_to_tensor(difficulty, dtype=tf.int32)

    # NOTE: This function might be called by an online data loader in a
    # tf.py_function wrapping fashion. But tf.py_function doesn't support
    # dict return type, so we have to return a sequence of unpacked.
    return classes, ymin, xmin, ymax, xmax, heading, z, height, difficulty