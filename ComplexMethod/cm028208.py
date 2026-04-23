def _generate(self, feature_map_shape_list, im_height=1, im_width=1):
    """Generates a collection of bounding boxes to be used as anchors.

    The number of anchors generated for a single grid with shape MxM where we
    place k boxes over each grid center is k*M^2 and thus the total number of
    anchors is the sum over all grids. In our box_specs_list example
    (see the constructor docstring), we would place two boxes over each grid
    point on an 8x8 grid and three boxes over each grid point on a 4x4 grid and
    thus end up with 2*8^2 + 3*4^2 = 176 anchors in total. The layout of the
    output anchors follows the order of how the grid sizes and box_specs are
    specified (with box_spec index varying the fastest, followed by width
    index, then height index, then grid index).

    Args:
      feature_map_shape_list: list of pairs of convnet layer resolutions in the
        format [(height_0, width_0), (height_1, width_1), ...]. For example,
        setting feature_map_shape_list=[(8, 8), (7, 7)] asks for anchors that
        correspond to an 8x8 layer followed by a 7x7 layer.
      im_height: the height of the image to generate the grid for. If both
        im_height and im_width are 1, the generated anchors default to
        absolute coordinates, otherwise normalized coordinates are produced.
      im_width: the width of the image to generate the grid for. If both
        im_height and im_width are 1, the generated anchors default to
        absolute coordinates, otherwise normalized coordinates are produced.

    Returns:
      boxes_list: a list of BoxLists each holding anchor boxes corresponding to
        the input feature map shapes.

    Raises:
      ValueError: if feature_map_shape_list, box_specs_list do not have the same
        length.
      ValueError: if feature_map_shape_list does not consist of pairs of
        integers
    """
    if not (isinstance(feature_map_shape_list, list)
            and len(feature_map_shape_list) == len(self._box_specs)):
      raise ValueError('feature_map_shape_list must be a list with the same '
                       'length as self._box_specs')
    if not all([isinstance(list_item, tuple) and len(list_item) == 2
                for list_item in feature_map_shape_list]):
      raise ValueError('feature_map_shape_list must be a list of pairs.')

    im_height = tf.cast(im_height, dtype=tf.float32)
    im_width = tf.cast(im_width, dtype=tf.float32)

    if not self._anchor_strides:
      anchor_strides = [(1.0 / tf.cast(pair[0], dtype=tf.float32),
                         1.0 / tf.cast(pair[1], dtype=tf.float32))
                        for pair in feature_map_shape_list]
    else:
      anchor_strides = [(tf.cast(stride[0], dtype=tf.float32) / im_height,
                         tf.cast(stride[1], dtype=tf.float32) / im_width)
                        for stride in self._anchor_strides]
    if not self._anchor_offsets:
      anchor_offsets = [(0.5 * stride[0], 0.5 * stride[1])
                        for stride in anchor_strides]
    else:
      anchor_offsets = [(tf.cast(offset[0], dtype=tf.float32) / im_height,
                         tf.cast(offset[1], dtype=tf.float32) / im_width)
                        for offset in self._anchor_offsets]

    for arg, arg_name in zip([anchor_strides, anchor_offsets],
                             ['anchor_strides', 'anchor_offsets']):
      if not (isinstance(arg, list) and len(arg) == len(self._box_specs)):
        raise ValueError('%s must be a list with the same length '
                         'as self._box_specs' % arg_name)
      if not all([isinstance(list_item, tuple) and len(list_item) == 2
                  for list_item in arg]):
        raise ValueError('%s must be a list of pairs.' % arg_name)

    anchor_grid_list = []
    min_im_shape = tf.minimum(im_height, im_width)
    scale_height = min_im_shape / im_height
    scale_width = min_im_shape / im_width
    if not tf.is_tensor(self._base_anchor_size):
      base_anchor_size = [
          scale_height * tf.constant(self._base_anchor_size[0],
                                     dtype=tf.float32),
          scale_width * tf.constant(self._base_anchor_size[1],
                                    dtype=tf.float32)
      ]
    else:
      base_anchor_size = [
          scale_height * self._base_anchor_size[0],
          scale_width * self._base_anchor_size[1]
      ]
    for feature_map_index, (grid_size, scales, aspect_ratios, stride,
                            offset) in enumerate(
                                zip(feature_map_shape_list, self._scales,
                                    self._aspect_ratios, anchor_strides,
                                    anchor_offsets)):
      tiled_anchors = grid_anchor_generator.tile_anchors(
          grid_height=grid_size[0],
          grid_width=grid_size[1],
          scales=scales,
          aspect_ratios=aspect_ratios,
          base_anchor_size=base_anchor_size,
          anchor_stride=stride,
          anchor_offset=offset)
      if self._clip_window is not None:
        tiled_anchors = box_list_ops.clip_to_window(
            tiled_anchors, self._clip_window, filter_nonoverlapping=False)
      num_anchors_in_layer = tiled_anchors.num_boxes_static()
      if num_anchors_in_layer is None:
        num_anchors_in_layer = tiled_anchors.num_boxes()
      anchor_indices = feature_map_index * tf.ones([num_anchors_in_layer])
      tiled_anchors.add_field('feature_map_index', anchor_indices)
      anchor_grid_list.append(tiled_anchors)

    return anchor_grid_list