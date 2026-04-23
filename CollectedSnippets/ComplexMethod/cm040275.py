def test_application_base(self, app, _, app_module, image_data_format):
        import tensorflow as tf

        if app == nasnet.NASNetMobile and backend.backend() == "torch":
            self.skipTest(
                "NASNetMobile pretrained incorrect with torch backend."
            )
        if (
            image_data_format == "channels_first"
            and len(tf.config.list_physical_devices("GPU")) == 0
            and backend.backend() == "tensorflow"
        ):
            self.skipTest(
                "Conv2D doesn't support channels_first using CPU with "
                "tensorflow backend"
            )
        self.skip_if_invalid_image_data_format_for_model(app, image_data_format)
        backend.set_image_data_format(image_data_format)

        # Can be instantiated with default arguments
        model = app(weights="imagenet")

        # Can run a correct inference on a test image
        if image_data_format == "channels_first":
            shape = model.input_shape[2:4]
        else:
            shape = model.input_shape[1:3]
        x = _get_elephant(shape)

        x = app_module.preprocess_input(x)
        preds = model.predict(x)
        names = [p[1] for p in app_module.decode_predictions(preds)[0]]
        # Test correct label is in top 3 (weak correctness test).
        self.assertIn("African_elephant", names[:3])

        # Can be serialized and deserialized
        config = serialization_lib.serialize_keras_object(model)
        reconstructed_model = serialization_lib.deserialize_keras_object(config)
        self.assertEqual(len(model.weights), len(reconstructed_model.weights))