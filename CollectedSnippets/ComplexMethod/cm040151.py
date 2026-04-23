def test_dynamic_shapes_export(self, model_type, dynamic_type):
        """Test ONNX export with various dynamic shape configurations.

        Tests two scenarios:
        - batch_only: Only batch dimension is dynamic, spatial dims fixed
        - height_width: Batch, height, width are dynamic, channels fixed
        """

        temp_filepath = os.path.join(self.get_temp_dir(), "exported_model")

        # Define input shapes based on dynamic type
        if dynamic_type == "batch_only":
            input_shape = (32, 32, 3)  # Only batch is dynamic (None)
            test_shapes = [(1, 32, 32, 3), (2, 32, 32, 3), (4, 32, 32, 3)]
        elif dynamic_type == "height_width":
            input_shape = (None, None, 3)  # Height and width are dynamic
            test_shapes = [(1, 28, 28, 3), (1, 64, 64, 3), (1, 128, 96, 3)]

        # Create model with appropriate layers for dynamic shapes
        layer_list = [
            layers.Conv2D(16, 3, padding="same", activation="relu"),
            layers.GlobalAveragePooling2D(),
            layers.Dense(10, activation="softmax"),
        ]

        if model_type == "sequential":
            model = models.Sequential(
                [layers.Input(shape=input_shape)] + layer_list
            )
        elif model_type == "functional":
            input_layer = layers.Input(shape=input_shape)
            output = input_layer
            for layer in layer_list:
                output = layer(output)
            model = models.Model(inputs=input_layer, outputs=output)

        # Build model with initial input
        initial_input = np.random.normal(size=test_shapes[0]).astype(np.float32)
        model(initial_input)

        # Export to ONNX
        onnx.export_onnx(model, temp_filepath)

        # Verify with ONNX Runtime
        ort_session = onnxruntime.InferenceSession(temp_filepath)
        input_info = ort_session.get_inputs()[0]

        # Check that dynamic dimensions are preserved
        input_shape_onnx = input_info.shape
        if dynamic_type == "batch_only":
            # Batch should be dynamic, others static
            self.assertTrue(isinstance(input_shape_onnx[0], str))  # Dynamic
            self.assertEqual(input_shape_onnx[1:], [32, 32, 3])  # Static
        elif dynamic_type == "height_width":
            # Batch, height, width should be dynamic, channels static
            self.assertTrue(isinstance(input_shape_onnx[0], str))  # Dynamic
            self.assertTrue(isinstance(input_shape_onnx[1], str))  # Dynamic
            self.assertTrue(isinstance(input_shape_onnx[2], str))  # Dynamic
            self.assertEqual(input_shape_onnx[3], 3)  # Static

        # Test inference with different input shapes
        for test_shape in test_shapes:
            test_input = np.random.randn(*test_shape).astype(np.float32)
            ort_inputs = {input_info.name: test_input}
            result = ort_session.run(None, ort_inputs)

            # Verify output shape matches expected batch size
            expected_batch_size = test_shape[0]
            self.assertEqual(result[0].shape[0], expected_batch_size)
            self.assertEqual(result[0].shape[1], 10)