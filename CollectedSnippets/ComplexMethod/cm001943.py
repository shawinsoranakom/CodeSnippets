def test_image_processor_preprocess_arguments(self):
        is_tested = False

        for image_processing_class in self.image_processing_classes.values():
            image_processor = image_processing_class(**self.image_processor_dict)

            # validation done by _valid_processor_keys attribute
            if hasattr(image_processor, "_valid_processor_keys") and hasattr(image_processor, "preprocess"):
                preprocess_parameter_names = inspect.getfullargspec(image_processor.preprocess).args
                preprocess_parameter_names.remove("self")
                preprocess_parameter_names.sort()
                valid_processor_keys = image_processor._valid_processor_keys
                valid_processor_keys.sort()
                self.assertEqual(preprocess_parameter_names, valid_processor_keys)
                is_tested = True

            # validation done by @filter_out_non_signature_kwargs decorator
            if hasattr(image_processor.preprocess, "_filter_out_non_signature_kwargs"):
                inputs = self.image_processor_tester.prepare_image_inputs()
                image = inputs[0]
                trimap = np.random.randint(0, 3, size=image.size[::-1])

                with warnings.catch_warnings(record=True) as raised_warnings:
                    warnings.simplefilter("always")
                    image_processor(image, trimaps=trimap, extra_argument=True)

                messages = " ".join([str(w.message) for w in raised_warnings])
                self.assertGreaterEqual(len(raised_warnings), 1)
                self.assertIn("extra_argument", messages)
                is_tested = True

            # ViTMatte-specific: validation for processors requiring trimaps (no _filter_out_non_signature_kwargs)
            if "trimaps" in inspect.signature(image_processor.preprocess).parameters:
                inputs = self.image_processor_tester.prepare_image_inputs()
                image = inputs[0]
                trimap = np.random.randint(0, 3, size=image.size[::-1])

                # Extra kwargs are rejected (TypeError for strict validation, or warning)
                with self.assertRaises(TypeError):
                    image_processor(image, trimaps=trimap, extra_argument=True)
                is_tested = True

        if not is_tested:
            self.skipTest(reason="No validation found for `preprocess` method")