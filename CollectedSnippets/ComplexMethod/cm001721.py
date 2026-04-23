def test_processor_with_multiple_inputs(self):
        """
        Tests that processor correctly handles multiple modality inputs together.
        Verifies that the output contains expected keys and raises error when no input is provided.
        """
        # Skip if processor doesn't have multiple attributes (not multimodal)
        attributes = self.processor_class.get_attributes()
        if len(attributes) <= 1:
            self.skipTest(f"Processor only has {len(attributes)} attribute(s), test requires multimodal processor")

        processor = self.get_processor()

        # Map attributes to input parameter names, prepare methods, and output key names
        attr_to_input_param = {
            "tokenizer": ("text", "prepare_text_inputs", "text_input_name"),
            "image_processor": ("images", "prepare_image_inputs", "images_input_name"),
            "video_processor": ("videos", "prepare_video_inputs", "videos_input_name"),
            "feature_extractor": ("audio", "prepare_audio_inputs", "audio_input_name"),
            "audio_processor": ("audio", "prepare_audio_inputs", "audio_input_name"),
        }

        # Prepare inputs dynamically based on processor attributes
        processor_inputs = {}
        expected_output_keys = []

        for attr in attributes:
            if attr in attr_to_input_param:
                param_name, prepare_method_name, output_key_attr = attr_to_input_param[attr]
                # Call the prepare method
                prepare_method = getattr(self, prepare_method_name)
                if param_name == "text":
                    modalities = []
                    if "image_processor" in attributes:
                        modalities.append("image")
                    if "video_processor" in attributes:
                        modalities.append("video")
                    if "audio_processor" in attributes or "feature_extractor" in attributes:
                        modalities.append("audio")
                    processor_inputs[param_name] = prepare_method(modalities=modalities)
                else:
                    processor_inputs[param_name] = prepare_method()
                # Track expected output keys
                expected_output_keys.append(getattr(self, output_key_attr))

        # Test combined processing
        inputs = processor(**processor_inputs, return_tensors="pt")

        # Verify output contains all expected keys
        for key in expected_output_keys:
            if key == self.audio_input_name:
                self.assertTrue(
                    self.audio_input_name_values in inputs or self.audio_input_name in inputs,
                    f"Expected either '{self.audio_input_name_values}' or '{self.audio_input_name}' in inputs",
                )
            else:
                self.assertIn(key, inputs)

        # Test that it raises error when no input is passed
        with self.assertRaises((TypeError, ValueError)):
            processor()