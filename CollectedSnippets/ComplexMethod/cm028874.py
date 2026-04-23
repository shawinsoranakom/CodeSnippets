def serve(self, images: tf.Tensor):
    """Casts image to float and runs inference.

    Args:
      images: uint8 Tensor of shape [batch_size, None, None, 3]

    Returns:
      Tensor holding detection output logits.
    """

    # Skip image preprocessing when input_type is tflite so it is compatible
    # with TFLite quantization.
    if self._input_type != 'tflite':
      images, anchor_boxes, image_info = self.preprocess(images)
    else:
      with tf.device('cpu:0'):
        anchor_boxes = self._build_anchor_boxes()
        # image_info is a 3D tensor of shape [batch_size, 4, 2]. It is in the
        # format of [[original_height, original_width],
        # [desired_height, desired_width], [y_scale, x_scale],
        # [y_offset, x_offset]]. When input_type is tflite, input image is
        # supposed to be preprocessed already.
        image_info = tf.convert_to_tensor(
            [[
                self._input_image_size,
                self._input_image_size,
                [1.0, 1.0],
                [0, 0],
            ]],
            dtype=tf.float32,
        )
    input_image_shape = image_info[:, 1, :]

    # To overcome keras.Model extra limitation to save a model with layers that
    # have multiple inputs, we use `model.call` here to trigger the forward
    # path. Note that, this disables some keras magics happens in `__call__`.
    model_call_kwargs = {
        'images': images,
        'image_shape': input_image_shape,
        'anchor_boxes': anchor_boxes,
        'training': False,
    }
    if isinstance(self.params.task.model, configs.retinanet.RetinaNet):
      model_call_kwargs['output_intermediate_features'] = (
          self.params.task.export_config.output_intermediate_features
      )
    detections = self.model.call(**model_call_kwargs)

    if self.params.task.model.detection_generator.apply_nms:
      # For RetinaNet model, apply export_config.
      # TODO(huizhongc): Add export_config to fasterrcnn and maskrcnn as needed.
      if isinstance(self.params.task.model, configs.retinanet.RetinaNet):
        export_config = self.params.task.export_config
        # Normalize detection box coordinates to [0, 1].
        if export_config.output_normalized_coordinates:
          keys = ['detection_boxes', 'detection_outer_boxes']
          detections = self._normalize_coordinates(detections, keys, image_info)

        # Cast num_detections and detection_classes to float. This allows the
        # model inference to work on chain (go/chain) as chain requires floating
        # point outputs.
        if export_config.cast_num_detections_to_float:
          detections['num_detections'] = tf.cast(
              detections['num_detections'], dtype=tf.float32
          )
        if export_config.cast_detection_classes_to_float:
          detections['detection_classes'] = tf.cast(
              detections['detection_classes'], dtype=tf.float32
          )

      final_outputs = {
          'detection_boxes': detections['detection_boxes'],
          'detection_scores': detections['detection_scores'],
          'detection_classes': detections['detection_classes'],
          'num_detections': detections['num_detections'],
      }
      if 'detection_outer_boxes' in detections:
        final_outputs['detection_outer_boxes'] = detections[
            'detection_outer_boxes'
        ]
    elif (
        isinstance(self.params.task.model, configs.retinanet.RetinaNet)
        and not self.params.task.model.detection_generator.decode_boxes
    ):
      final_outputs = {
          'raw_boxes': self._flatten_output(detections['box_outputs'], 4),
          'raw_scores': tf.sigmoid(
              self._flatten_output(
                  detections['cls_outputs'], self.params.task.model.num_classes
              )
          ),
      }
    else:
      # For RetinaNet model, apply export_config.
      if isinstance(self.params.task.model, configs.retinanet.RetinaNet):
        export_config = self.params.task.export_config
        # Normalize detection box coordinates to [0, 1].
        if export_config.output_normalized_coordinates:
          keys = ['decoded_boxes']
          detections = self._normalize_coordinates(detections, keys, image_info)
      final_outputs = {
          'decoded_boxes': detections['decoded_boxes'],
          'decoded_box_scores': detections['decoded_box_scores'],
      }

    if 'detection_masks' in detections.keys():
      final_outputs['detection_masks'] = detections['detection_masks']
    if (
        isinstance(self.params.task.model, configs.retinanet.RetinaNet)
        and self.params.task.export_config.output_intermediate_features
    ):
      final_outputs.update(
          {
              k: v
              for k, v in detections.items()
              if k.startswith('backbone_') or k.startswith('decoder_')
          }
      )

    if self.params.task.model.detection_generator.nms_version != 'tflite':
      final_outputs.update({'image_info': image_info})
    return final_outputs