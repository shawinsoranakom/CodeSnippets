def __init__(self,
               box_specs_list,
               base_anchor_size=None,
               anchor_strides=None,
               anchor_offsets=None,
               clip_window=None):
    """Constructs a MultipleGridAnchorGenerator.

    To construct anchors, at multiple grid resolutions, one must provide a
    list of feature_map_shape_list (e.g., [(8, 8), (4, 4)]), and for each grid
    size, a corresponding list of (scale, aspect ratio) box specifications.

    For example:
    box_specs_list = [[(.1, 1.0), (.1, 2.0)],  # for 8x8 grid
                      [(.2, 1.0), (.3, 1.0), (.2, 2.0)]]  # for 4x4 grid

    To support the fully convolutional setting, we pass grid sizes in at
    generation time, while scale and aspect ratios are fixed at construction
    time.

    Args:
      box_specs_list: list of list of (scale, aspect ratio) pairs with the
        outside list having the same number of entries as feature_map_shape_list
        (which is passed in at generation time).
      base_anchor_size: base anchor size as [height, width]
                        (length-2 float numpy or Tensor, default=[1.0, 1.0]).
                        The height and width values are normalized to the
                        minimum dimension of the input height and width, so that
                        when the base anchor height equals the base anchor
                        width, the resulting anchor is square even if the input
                        image is not square.
      anchor_strides: list of pairs of strides in pixels (in y and x directions
        respectively). For example, setting anchor_strides=[(25, 25), (50, 50)]
        means that we want the anchors corresponding to the first layer to be
        strided by 25 pixels and those in the second layer to be strided by 50
        pixels in both y and x directions. If anchor_strides=None, they are set
        to be the reciprocal of the corresponding feature map shapes.
      anchor_offsets: list of pairs of offsets in pixels (in y and x directions
        respectively). The offset specifies where we want the center of the
        (0, 0)-th anchor to lie for each layer. For example, setting
        anchor_offsets=[(10, 10), (20, 20)]) means that we want the
        (0, 0)-th anchor of the first layer to lie at (10, 10) in pixel space
        and likewise that we want the (0, 0)-th anchor of the second layer to
        lie at (25, 25) in pixel space. If anchor_offsets=None, then they are
        set to be half of the corresponding anchor stride.
      clip_window: a tensor of shape [4] specifying a window to which all
        anchors should be clipped. If clip_window is None, then no clipping
        is performed.

    Raises:
      ValueError: if box_specs_list is not a list of list of pairs
      ValueError: if clip_window is not either None or a tensor of shape [4]
    """
    if isinstance(box_specs_list, list) and all(
        [isinstance(list_item, list) for list_item in box_specs_list]):
      self._box_specs = box_specs_list
    else:
      raise ValueError('box_specs_list is expected to be a '
                       'list of lists of pairs')
    if base_anchor_size is None:
      base_anchor_size = [256, 256]
    self._base_anchor_size = base_anchor_size
    self._anchor_strides = anchor_strides
    self._anchor_offsets = anchor_offsets
    if clip_window is not None and clip_window.get_shape().as_list() != [4]:
      raise ValueError('clip_window must either be None or a shape [4] tensor')
    self._clip_window = clip_window
    self._scales = []
    self._aspect_ratios = []
    for box_spec in self._box_specs:
      if not all([isinstance(entry, tuple) and len(entry) == 2
                  for entry in box_spec]):
        raise ValueError('box_specs_list is expected to be a '
                         'list of lists of pairs')
      scales, aspect_ratios = zip(*box_spec)
      self._scales.append(scales)
      self._aspect_ratios.append(aspect_ratios)

    for arg, arg_name in zip([self._anchor_strides, self._anchor_offsets],
                             ['anchor_strides', 'anchor_offsets']):
      if arg and not (isinstance(arg, list) and
                      len(arg) == len(self._box_specs)):
        raise ValueError('%s must be a list with the same length '
                         'as self._box_specs' % arg_name)
      if arg and not all([
          isinstance(list_item, tuple) and len(list_item) == 2
          for list_item in arg
      ]):
        raise ValueError('%s must be a list of pairs.' % arg_name)