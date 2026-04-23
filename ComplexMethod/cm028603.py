def test_builder(self,
                   backbone_type,
                   decoder_type,
                   input_size,
                   quantize_detection_head,
                   quantize_detection_decoder):
    num_classes = 2
    input_specs = tf_keras.layers.InputSpec(
        shape=[None, input_size[0], input_size[1], 3])

    if backbone_type == 'spinenet_mobile':
      backbone_config = backbones.Backbone(
          type=backbone_type,
          spinenet_mobile=backbones.SpineNetMobile(
              model_id='49',
              stochastic_depth_drop_rate=0.2,
              min_level=3,
              max_level=7,
              use_keras_upsampling_2d=True))
    elif backbone_type == 'mobilenet':
      backbone_config = backbones.Backbone(
          type=backbone_type,
          mobilenet=backbones.MobileNet(
              model_id='MobileNetV2',
              filter_size_scale=1.0))
    else:
      raise ValueError(
          'backbone_type {} is not supported'.format(backbone_type))

    if decoder_type == 'identity':
      decoder_config = decoders.Decoder(type=decoder_type)
    elif decoder_type == 'fpn':
      decoder_config = decoders.Decoder(
          type=decoder_type,
          fpn=decoders.FPN(
              num_filters=128,
              use_separable_conv=True,
              use_keras_layer=True))
    else:
      raise ValueError(
          'decoder_type {} is not supported'.format(decoder_type))

    model_config = retinanet_cfg.RetinaNet(
        num_classes=num_classes,
        input_size=[input_size[0], input_size[1], 3],
        backbone=backbone_config,
        decoder=decoder_config,
        head=retinanet_cfg.RetinaNetHead(
            attribute_heads=None,
            use_separable_conv=True))

    l2_regularizer = tf_keras.regularizers.l2(5e-5)
    # Build the original float32 retinanet model.
    model = factory.build_retinanet(
        input_specs=input_specs,
        model_config=model_config,
        l2_regularizer=l2_regularizer)

    # Call the model with dummy input to build the head part.
    dummpy_input = tf.zeros([1] + model_config.input_size)
    model(dummpy_input, training=True)

    # Build the QAT model from the original model with quantization config.
    qat_model = qat_factory.build_qat_retinanet(
        model=model,
        quantization=common.Quantization(
            quantize_detection_decoder=quantize_detection_decoder,
            quantize_detection_head=quantize_detection_head),
        model_config=model_config)

    if quantize_detection_head:
      # head become a RetinaNetHeadQuantized when we apply quantization.
      self.assertIsInstance(qat_model.head,
                            qat_dense_prediction_heads.RetinaNetHeadQuantized)
    else:
      # head is a RetinaNetHead if we don't apply quantization on head part.
      self.assertIsInstance(
          qat_model.head, dense_prediction_heads.RetinaNetHead)
      self.assertNotIsInstance(
          qat_model.head, qat_dense_prediction_heads.RetinaNetHeadQuantized)

    if decoder_type == 'FPN':
      if quantize_detection_decoder:
        # FPN decoder become a general keras functional model after applying
        # quantization.
        self.assertNotIsInstance(qat_model.decoder, fpn.FPN)
      else:
        self.assertIsInstance(qat_model.decoder, fpn.FPN)