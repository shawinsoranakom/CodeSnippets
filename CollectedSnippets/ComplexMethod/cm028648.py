def __init__(self,
               anchors=None,
               anchor_free_level_limits=None,
               level_strides=None,
               center_radius=None,
               max_num_instances=200,
               match_threshold=0.25,
               best_matches_only=False,
               use_tie_breaker=True,
               darknet=False,
               dtype='float32'):
    """Initialization for anchor labler.

    Args:
      anchors: `Dict[List[Union[int, float]]]` values for each anchor box.
      anchor_free_level_limits: `List` the box sizes that will be allowed at
        each FPN level as is done in the FCOS and YOLOX paper for anchor free
        box assignment.
      level_strides: `Dict[int]` for how much the model scales down the images
        at the each level.
      center_radius: `Dict[float]` for radius around each box center to search
        for extra centers in each level.
      max_num_instances: `int` for the number of boxes to compute loss on.
      match_threshold: `float` indicating the threshold over which an anchor
        will be considered for prediction, at zero, all the anchors will be used
        and at 1.0 only the best will be used. for anchor thresholds larger than
        1.0 we stop using the IOU for anchor comparison and resort directly to
        comparing the width and height, this is used for the scaled models.
      best_matches_only: `boolean` indicating how boxes are selected for
        optimization.
      use_tie_breaker: `boolean` indicating whether to use the anchor threshold
        value.
      darknet: `boolean` indicating which data pipeline to use. Setting to True
        swaps the pipeline to output images realtive to Yolov4 and older.
      dtype: `str` indicating the output datatype of the datapipeline selecting
        from {"float32", "float16", "bfloat16"}.
    """
    self.anchors = anchors
    self.masks = self._get_mask()
    self.anchor_free_level_limits = self._get_level_limits(
        anchor_free_level_limits)

    if darknet and self.anchor_free_level_limits is None:
      center_radius = None

    self.keys = self.anchors.keys()
    if self.anchor_free_level_limits is not None:
      maxim = 2000
      match_threshold = -0.01
      self.num_instances = {key: maxim for key in self.keys}
    elif not darknet:
      self.num_instances = {
          key: (6 - i) * max_num_instances for i, key in enumerate(self.keys)
      }
    else:
      self.num_instances = {key: max_num_instances for key in self.keys}

    self.center_radius = center_radius
    self.level_strides = level_strides
    self.match_threshold = match_threshold
    self.best_matches_only = best_matches_only
    self.use_tie_breaker = use_tie_breaker
    self.dtype = dtype