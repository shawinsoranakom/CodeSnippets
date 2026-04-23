def __init__(self, params):
    super(OlnMaskModel, self).__init__(params)

    self._params = params

    # Different heads and layers.
    self._include_rpn_class = params.architecture.include_rpn_class
    self._include_mask = params.architecture.include_mask
    self._include_frcnn_class = params.architecture.include_frcnn_class
    self._include_frcnn_box = params.architecture.include_frcnn_box
    self._include_centerness = params.rpn_head.has_centerness
    self._include_box_score = (params.frcnn_head.has_scoring and
                               params.architecture.include_frcnn_box)
    self._include_mask_score = (params.mrcnn_head.has_scoring and
                                params.architecture.include_mask)

    # Architecture generators.
    self._backbone_fn = factory.backbone_generator(params)
    self._fpn_fn = factory.multilevel_features_generator(params)
    self._rpn_head_fn = factory.rpn_head_generator(params)
    if self._include_centerness:
      self._rpn_head_fn = factory.oln_rpn_head_generator(params)
    else:
      self._rpn_head_fn = factory.rpn_head_generator(params)
    self._generate_rois_fn = roi_ops.OlnROIGenerator(params.roi_proposal)
    self._sample_rois_fn = target_ops.ROIScoreSampler(params.roi_sampling)
    self._sample_masks_fn = target_ops.MaskSampler(
        params.architecture.mask_target_size,
        params.mask_sampling.num_mask_samples_per_image)

    if self._include_box_score:
      self._frcnn_head_fn = factory.oln_box_score_head_generator(params)
    else:
      self._frcnn_head_fn = factory.fast_rcnn_head_generator(params)

    if self._include_mask:
      if self._include_mask_score:
        self._mrcnn_head_fn = factory.oln_mask_score_head_generator(params)
      else:
        self._mrcnn_head_fn = factory.mask_rcnn_head_generator(params)

    # Loss function.
    self._rpn_score_loss_fn = losses.RpnScoreLoss(params.rpn_score_loss)
    self._rpn_box_loss_fn = losses.RpnBoxLoss(params.rpn_box_loss)
    if self._include_centerness:
      self._rpn_iou_loss_fn = losses.OlnRpnIoULoss()
      self._rpn_center_loss_fn = losses.OlnRpnCenterLoss()
    self._frcnn_class_loss_fn = losses.FastrcnnClassLoss()
    self._frcnn_box_loss_fn = losses.FastrcnnBoxLoss(params.frcnn_box_loss)
    if self._include_box_score:
      self._frcnn_box_score_loss_fn = losses.OlnBoxScoreLoss(
          params.frcnn_box_score_loss)
    if self._include_mask:
      self._mask_loss_fn = losses.MaskrcnnLoss()

    self._generate_detections_fn = postprocess_ops.OlnDetectionGenerator(
        params.postprocess)

    self._transpose_input = params.train.transpose_input
    assert not self._transpose_input, 'Transpose input is not supportted.'