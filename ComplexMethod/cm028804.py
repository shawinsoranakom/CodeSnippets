def test_forward(self, strategy, image_size, training, has_att_heads,
                   output_intermediate_features, soft_nms_sigma):
    """Test for creation of a R50-FPN RetinaNet."""
    tf_keras.backend.set_image_data_format('channels_last')
    num_classes = 3
    min_level = 3
    max_level = 7
    num_scales = 3
    aspect_ratios = [1.0]
    num_anchors_per_location = num_scales * len(aspect_ratios)

    images = np.random.rand(2, image_size[0], image_size[1], 3)
    image_shape = np.array(
        [[image_size[0], image_size[1]], [image_size[0], image_size[1]]])

    with strategy.scope():
      anchor_gen = anchor.build_anchor_generator(
          min_level=min_level,
          max_level=max_level,
          num_scales=num_scales,
          aspect_ratios=aspect_ratios,
          anchor_size=3)
      anchor_boxes = anchor_gen(image_size)
      for l in anchor_boxes:
        anchor_boxes[l] = tf.tile(
            tf.expand_dims(anchor_boxes[l], axis=0), [2, 1, 1, 1])

      backbone = resnet.ResNet(model_id=50)
      decoder = fpn.FPN(
          input_specs=backbone.output_specs,
          min_level=min_level,
          max_level=max_level)

      if has_att_heads:
        attribute_heads = [
            dict(
                name='depth',
                type='regression',
                size=1,
                prediction_tower_name='')
        ]
      else:
        attribute_heads = None
      head = dense_prediction_heads.RetinaNetHead(
          min_level=min_level,
          max_level=max_level,
          num_classes=num_classes,
          attribute_heads=attribute_heads,
          num_anchors_per_location=num_anchors_per_location)
      generator = detection_generator.MultilevelDetectionGenerator(
          max_num_detections=10,
          nms_version='v1',
          use_cpu_nms=soft_nms_sigma is not None,
          soft_nms_sigma=soft_nms_sigma)
      model = retinanet_model.RetinaNetModel(
          backbone=backbone,
          decoder=decoder,
          head=head,
          detection_generator=generator)

      model_outputs = model(
          images,
          image_shape,
          anchor_boxes,
          output_intermediate_features=output_intermediate_features,
          training=training)

    if training:
      cls_outputs = model_outputs['cls_outputs']
      box_outputs = model_outputs['box_outputs']
      for level in range(min_level, max_level + 1):
        self.assertIn(str(level), cls_outputs)
        self.assertIn(str(level), box_outputs)
        self.assertAllEqual([
            2,
            image_size[0] // 2**level,
            image_size[1] // 2**level,
            num_classes * num_anchors_per_location
        ], cls_outputs[str(level)].numpy().shape)
        self.assertAllEqual([
            2,
            image_size[0] // 2**level,
            image_size[1] // 2**level,
            4 * num_anchors_per_location
        ], box_outputs[str(level)].numpy().shape)
        if has_att_heads:
          att_outputs = model_outputs['attribute_outputs']
          for att in att_outputs.values():
            self.assertAllEqual([
                2, image_size[0] // 2**level, image_size[1] // 2**level,
                1 * num_anchors_per_location
            ], att[str(level)].numpy().shape)
    else:
      self.assertIn('detection_boxes', model_outputs)
      self.assertIn('detection_scores', model_outputs)
      self.assertIn('detection_classes', model_outputs)
      self.assertIn('num_detections', model_outputs)
      self.assertAllEqual(
          [2, 10, 4], model_outputs['detection_boxes'].numpy().shape)
      self.assertAllEqual(
          [2, 10], model_outputs['detection_scores'].numpy().shape)
      self.assertAllEqual(
          [2, 10], model_outputs['detection_classes'].numpy().shape)
      self.assertAllEqual(
          [2,], model_outputs['num_detections'].numpy().shape)
      if has_att_heads:
        self.assertIn('detection_attributes', model_outputs)
        self.assertAllEqual(
            [2, 10, 1],
            model_outputs['detection_attributes']['depth'].numpy().shape)
    if output_intermediate_features:
      for l in range(2, 6):
        self.assertIn('backbone_{}'.format(l), model_outputs)
        self.assertAllEqual([
            2, image_size[0] // 2**l, image_size[1] // 2**l,
            backbone.output_specs[str(l)].as_list()[-1]
        ], model_outputs['backbone_{}'.format(l)].numpy().shape)
      for l in range(min_level, max_level + 1):
        self.assertIn('decoder_{}'.format(l), model_outputs)
        self.assertAllEqual([
            2, image_size[0] // 2**l, image_size[1] // 2**l,
            decoder.output_specs[str(l)].as_list()[-1]
        ], model_outputs['decoder_{}'.format(l)].numpy().shape)