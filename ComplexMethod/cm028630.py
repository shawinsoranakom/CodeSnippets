def test_model_with_customized_kernel_initializer(self):
    self.model_config.conv_kernel_initializer = 'he_uniform'
    self.model_config.dense_kernel_initializer = 'glorot_normal'
    model_input = tf_keras.layers.Input(shape=(224, 224, 1))
    model_output = mobilenet_edgetpu_v2_model_blocks.mobilenet_edgetpu_v2(
        image_input=model_input,
        config=self.model_config)
    test_model = tf_keras.Model(inputs=model_input, outputs=model_output)

    conv_layer_stack = []
    for layer in test_model.layers:
      if (isinstance(layer, tf_keras.layers.Conv2D) or
          isinstance(layer, tf_keras.layers.DepthwiseConv2D) or
          isinstance(layer, custom_layers.GroupConv2D)):
        conv_layer_stack.append(layer)
    self.assertGreater(len(conv_layer_stack), 2)
    # The last Conv layer is used as a Dense layer.
    for layer in conv_layer_stack[:-1]:
      if isinstance(layer, custom_layers.GroupConv2D):
        self.assertIsInstance(layer.kernel_initializer,
                              tf_keras.initializers.GlorotUniform)
      elif isinstance(layer, tf_keras.layers.Conv2D):
        self.assertIsInstance(layer.kernel_initializer,
                              tf_keras.initializers.HeUniform)
      elif isinstance(layer, tf_keras.layers.DepthwiseConv2D):
        self.assertIsInstance(layer.depthwise_initializer,
                              tf_keras.initializers.HeUniform)

    self.assertIsInstance(conv_layer_stack[-1].kernel_initializer,
                          tf_keras.initializers.GlorotNormal)