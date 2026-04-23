def test_forward(self, strategy, include_mask, build_anchor_boxes, training,
                   use_cascade_heads):
    num_classes = 3
    min_level = 3
    max_level = 4
    num_scales = 3
    aspect_ratios = [1.0]
    anchor_size = 3
    if use_cascade_heads:
      cascade_iou_thresholds = [0.6]
      class_agnostic_bbox_pred = True
      cascade_class_ensemble = True
    else:
      cascade_iou_thresholds = None
      class_agnostic_bbox_pred = False
      cascade_class_ensemble = False

    image_size = (256, 256)
    images = np.random.rand(2, image_size[0], image_size[1], 3)
    image_shape = np.array([[224, 100], [100, 224]])
    with strategy.scope():
      if build_anchor_boxes:
        anchor_boxes = anchor.Anchor(
            min_level=min_level,
            max_level=max_level,
            num_scales=num_scales,
            aspect_ratios=aspect_ratios,
            anchor_size=anchor_size,
            image_size=image_size).multilevel_boxes
      else:
        anchor_boxes = None
      num_anchors_per_location = len(aspect_ratios) * num_scales

      input_specs = tf_keras.layers.InputSpec(shape=[None, None, None, 3])
      backbone = resnet.ResNet(model_id=50, input_specs=input_specs)
      decoder = fpn.FPN(
          min_level=min_level,
          max_level=max_level,
          input_specs=backbone.output_specs)
      rpn_head = dense_prediction_heads.RPNHead(
          min_level=min_level,
          max_level=max_level,
          num_anchors_per_location=num_anchors_per_location)
      detection_head = instance_heads.DetectionHead(
          num_classes=num_classes,
          class_agnostic_bbox_pred=class_agnostic_bbox_pred)
      roi_generator_obj = roi_generator.MultilevelROIGenerator()

      roi_sampler_cascade = []
      roi_sampler_obj = roi_sampler.ROISampler()
      roi_sampler_cascade.append(roi_sampler_obj)
      if cascade_iou_thresholds:
        for iou in cascade_iou_thresholds:
          roi_sampler_obj = roi_sampler.ROISampler(
              mix_gt_boxes=False,
              foreground_iou_threshold=iou,
              background_iou_high_threshold=iou,
              background_iou_low_threshold=0.0,
              skip_subsampling=True)
          roi_sampler_cascade.append(roi_sampler_obj)
      roi_aligner_obj = roi_aligner.MultilevelROIAligner()
      detection_generator_obj = detection_generator.DetectionGenerator()
      if include_mask:
        mask_head = instance_heads.MaskHead(
            num_classes=num_classes, upsample_factor=2)
        mask_sampler_obj = mask_sampler.MaskSampler(
            mask_target_size=28, num_sampled_masks=1)
        mask_roi_aligner_obj = roi_aligner.MultilevelROIAligner(crop_size=14)
      else:
        mask_head = None
        mask_sampler_obj = None
        mask_roi_aligner_obj = None
      model = maskrcnn_model.MaskRCNNModel(
          backbone,
          decoder,
          rpn_head,
          detection_head,
          roi_generator_obj,
          roi_sampler_obj,
          roi_aligner_obj,
          detection_generator_obj,
          mask_head,
          mask_sampler_obj,
          mask_roi_aligner_obj,
          class_agnostic_bbox_pred=class_agnostic_bbox_pred,
          cascade_class_ensemble=cascade_class_ensemble,
          min_level=min_level,
          max_level=max_level,
          num_scales=num_scales,
          aspect_ratios=aspect_ratios,
          anchor_size=anchor_size)

      gt_boxes = np.array(
          [[[10, 10, 15, 15], [2.5, 2.5, 7.5, 7.5], [-1, -1, -1, -1]],
           [[100, 100, 150, 150], [-1, -1, -1, -1], [-1, -1, -1, -1]]],
          dtype=np.float32)
      gt_outer_boxes = np.array(
          [[[11, 11, 16.5, 16.5], [2.75, 2.75, 8.25, 8.25], [-1, -1, -1, -1]],
           [[110, 110, 165, 165], [-1, -1, -1, -1], [-1, -1, -1, -1]]],
          dtype=np.float32)
      gt_classes = np.array([[2, 1, -1], [1, -1, -1]], dtype=np.int32)
      if include_mask:
        gt_masks = np.ones((2, 3, 100, 100))
      else:
        gt_masks = None

      results = model(
          images,
          image_shape,
          anchor_boxes,
          gt_boxes,
          gt_classes,
          gt_masks,
          gt_outer_boxes,
          training=training)

    self.assertIn('rpn_boxes', results)
    self.assertIn('rpn_scores', results)
    if training:
      self.assertIn('class_targets', results)
      self.assertIn('box_targets', results)
      self.assertIn('class_outputs', results)
      self.assertIn('box_outputs', results)
      if include_mask:
        self.assertIn('mask_outputs', results)
    else:
      self.assertIn('detection_boxes', results)
      self.assertIn('detection_scores', results)
      self.assertIn('detection_classes', results)
      self.assertIn('num_detections', results)
      if include_mask:
        self.assertIn('detection_masks', results)