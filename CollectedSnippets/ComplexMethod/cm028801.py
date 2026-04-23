def __init__(self,
               backbone: tf_keras.Model,
               decoder: tf_keras.Model,
               rpn_head: tf_keras.layers.Layer,
               detection_head: Union[tf_keras.layers.Layer,
                                     List[tf_keras.layers.Layer]],
               roi_generator: tf_keras.layers.Layer,
               roi_sampler: Union[tf_keras.layers.Layer,
                                  List[tf_keras.layers.Layer]],
               roi_aligner: tf_keras.layers.Layer,
               detection_generator: tf_keras.layers.Layer,
               mask_head: Optional[tf_keras.layers.Layer] = None,
               mask_sampler: Optional[tf_keras.layers.Layer] = None,
               mask_roi_aligner: Optional[tf_keras.layers.Layer] = None,
               class_agnostic_bbox_pred: bool = False,
               cascade_class_ensemble: bool = False,
               min_level: Optional[int] = None,
               max_level: Optional[int] = None,
               num_scales: Optional[int] = None,
               aspect_ratios: Optional[List[float]] = None,
               anchor_size: Optional[float] = None,
               outer_boxes_scale: float = 1.0,
               **kwargs):
    """Initializes the R-CNN(-RS) model.

    Args:
      backbone: `tf_keras.Model`, the backbone network.
      decoder: `tf_keras.Model`, the decoder network.
      rpn_head: the RPN head.
      detection_head: the detection head or a list of heads.
      roi_generator: the ROI generator.
      roi_sampler: a single ROI sampler or a list of ROI samplers for cascade
        detection heads.
      roi_aligner: the ROI aligner.
      detection_generator: the detection generator.
      mask_head: the mask head.
      mask_sampler: the mask sampler.
      mask_roi_aligner: the ROI alginer for mask prediction.
      class_agnostic_bbox_pred: if True, perform class agnostic bounding box
        prediction. Needs to be `True` for Cascade RCNN models.
      cascade_class_ensemble: if True, ensemble classification scores over all
        detection heads.
      min_level: Minimum level in output feature maps.
      max_level: Maximum level in output feature maps.
      num_scales: A number representing intermediate scales added on each level.
        For instances, num_scales=2 adds one additional intermediate anchor
        scales [2^0, 2^0.5] on each level.
      aspect_ratios: A list representing the aspect raito anchors added on each
        level. The number indicates the ratio of width to height. For instances,
        aspect_ratios=[1.0, 2.0, 0.5] adds three anchors on each scale level.
      anchor_size: A number representing the scale of size of the base anchor to
        the feature stride 2^level.
      outer_boxes_scale: a float to scale up the bounding boxes to generate
        more inclusive masks. The scale is expected to be >=1.0.
      **kwargs: keyword arguments to be passed.
    """
    super().__init__(**kwargs)
    self._config_dict = {
        'backbone': backbone,
        'decoder': decoder,
        'rpn_head': rpn_head,
        'detection_head': detection_head,
        'roi_generator': roi_generator,
        'roi_sampler': roi_sampler,
        'roi_aligner': roi_aligner,
        'detection_generator': detection_generator,
        'outer_boxes_scale': outer_boxes_scale,
        'mask_head': mask_head,
        'mask_sampler': mask_sampler,
        'mask_roi_aligner': mask_roi_aligner,
        'class_agnostic_bbox_pred': class_agnostic_bbox_pred,
        'cascade_class_ensemble': cascade_class_ensemble,
        'min_level': min_level,
        'max_level': max_level,
        'num_scales': num_scales,
        'aspect_ratios': aspect_ratios,
        'anchor_size': anchor_size,
    }
    self.backbone = backbone
    self.decoder = decoder
    self.rpn_head = rpn_head
    if not isinstance(detection_head, (list, tuple)):
      self.detection_head = [detection_head]
    else:
      self.detection_head = detection_head
    self.roi_generator = roi_generator
    if not isinstance(roi_sampler, (list, tuple)):
      self.roi_sampler = [roi_sampler]
    else:
      self.roi_sampler = roi_sampler
    if len(self.roi_sampler) > 1 and not class_agnostic_bbox_pred:
      raise ValueError(
          '`class_agnostic_bbox_pred` needs to be True if multiple detection heads are specified.'
      )
    self.roi_aligner = roi_aligner
    self.detection_generator = detection_generator
    self._include_mask = mask_head is not None
    if outer_boxes_scale < 1.0:
      raise ValueError('`outer_boxes_scale` should be a value >= 1.0.')
    self.outer_boxes_scale = outer_boxes_scale
    self.mask_head = mask_head
    if self._include_mask and mask_sampler is None:
      raise ValueError('`mask_sampler` is not provided in Mask R-CNN.')
    self.mask_sampler = mask_sampler
    if self._include_mask and mask_roi_aligner is None:
      raise ValueError('`mask_roi_aligner` is not provided in Mask R-CNN.')
    self.mask_roi_aligner = mask_roi_aligner
    # Weights for the regression losses for each FRCNN layer.
    # TODO(jiageng): Make the weights configurable.
    self._cascade_layer_to_weights = [
        [10.0, 10.0, 5.0, 5.0],
        [20.0, 20.0, 10.0, 10.0],
        [30.0, 30.0, 15.0, 15.0],
    ]