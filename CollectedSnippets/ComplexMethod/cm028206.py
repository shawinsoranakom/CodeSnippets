def create_ssd_anchors(num_layers=6,
                       min_scale=0.2,
                       max_scale=0.95,
                       scales=None,
                       aspect_ratios=(1.0, 2.0, 3.0, 1.0 / 2, 1.0 / 3),
                       interpolated_scale_aspect_ratio=1.0,
                       base_anchor_size=None,
                       anchor_strides=None,
                       anchor_offsets=None,
                       reduce_boxes_in_lowest_layer=True):
  """Creates MultipleGridAnchorGenerator for SSD anchors.

  This function instantiates a MultipleGridAnchorGenerator that reproduces
  ``default box`` construction proposed by Liu et al in the SSD paper.
  See Section 2.2 for details. Grid sizes are assumed to be passed in
  at generation time from finest resolution to coarsest resolution --- this is
  used to (linearly) interpolate scales of anchor boxes corresponding to the
  intermediate grid sizes.

  Anchors that are returned by calling the `generate` method on the returned
  MultipleGridAnchorGenerator object are always in normalized coordinates
  and clipped to the unit square: (i.e. all coordinates lie in [0, 1]x[0, 1]).

  Args:
    num_layers: integer number of grid layers to create anchors for (actual
      grid sizes passed in at generation time)
    min_scale: scale of anchors corresponding to finest resolution (float)
    max_scale: scale of anchors corresponding to coarsest resolution (float)
    scales: As list of anchor scales to use. When not None and not empty,
      min_scale and max_scale are not used.
    aspect_ratios: list or tuple of (float) aspect ratios to place on each
      grid point.
    interpolated_scale_aspect_ratio: An additional anchor is added with this
      aspect ratio and a scale interpolated between the scale for a layer
      and the scale for the next layer (1.0 for the last layer).
      This anchor is not included if this value is 0.
    base_anchor_size: base anchor size as [height, width].
      The height and width values are normalized to the minimum dimension of the
      input height and width, so that when the base anchor height equals the
      base anchor width, the resulting anchor is square even if the input image
      is not square.
    anchor_strides: list of pairs of strides in pixels (in y and x directions
      respectively). For example, setting anchor_strides=[(25, 25), (50, 50)]
      means that we want the anchors corresponding to the first layer to be
      strided by 25 pixels and those in the second layer to be strided by 50
      pixels in both y and x directions. If anchor_strides=None, they are set to
      be the reciprocal of the corresponding feature map shapes.
    anchor_offsets: list of pairs of offsets in pixels (in y and x directions
      respectively). The offset specifies where we want the center of the
      (0, 0)-th anchor to lie for each layer. For example, setting
      anchor_offsets=[(10, 10), (20, 20)]) means that we want the
      (0, 0)-th anchor of the first layer to lie at (10, 10) in pixel space
      and likewise that we want the (0, 0)-th anchor of the second layer to lie
      at (25, 25) in pixel space. If anchor_offsets=None, then they are set to
      be half of the corresponding anchor stride.
    reduce_boxes_in_lowest_layer: a boolean to indicate whether the fixed 3
      boxes per location is used in the lowest layer.

  Returns:
    a MultipleGridAnchorGenerator
  """
  if base_anchor_size is None:
    base_anchor_size = [1.0, 1.0]
  box_specs_list = []
  if scales is None or not scales:
    scales = [min_scale + (max_scale - min_scale) * i / (num_layers - 1)
              for i in range(num_layers)] + [1.0]
  else:
    # Add 1.0 to the end, which will only be used in scale_next below and used
    # for computing an interpolated scale for the largest scale in the list.
    scales += [1.0]

  for layer, scale, scale_next in zip(
      range(num_layers), scales[:-1], scales[1:]):
    layer_box_specs = []
    if layer == 0 and reduce_boxes_in_lowest_layer:
      layer_box_specs = [(0.1, 1.0), (scale, 2.0), (scale, 0.5)]
    else:
      for aspect_ratio in aspect_ratios:
        layer_box_specs.append((scale, aspect_ratio))
      # Add one more anchor, with a scale between the current scale, and the
      # scale for the next layer, with a specified aspect ratio (1.0 by
      # default).
      if interpolated_scale_aspect_ratio > 0.0:
        layer_box_specs.append((np.sqrt(scale*scale_next),
                                interpolated_scale_aspect_ratio))
    box_specs_list.append(layer_box_specs)

  return MultipleGridAnchorGenerator(box_specs_list, base_anchor_size,
                                     anchor_strides, anchor_offsets)