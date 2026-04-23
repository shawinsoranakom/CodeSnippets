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
                if hasattr(self.image_processor_tester, "prepare_image_inputs"):
                    inputs = self.image_processor_tester.prepare_image_inputs()
                elif hasattr(self.image_processor_tester, "prepare_video_inputs"):
                    inputs = self.image_processor_tester.prepare_video_inputs()
                else:
                    self.skipTest(reason="No valid input preparation method found")

                with warnings.catch_warnings(record=True) as raised_warnings:
                    warnings.simplefilter("always")
                    image_processor(inputs, extra_argument=True)

                messages = " ".join([str(w.message) for w in raised_warnings])
                self.assertGreaterEqual(len(raised_warnings), 1)
                self.assertIn("extra_argument", messages)
                is_tested = True

        if not is_tested:
            self.skipTest(reason="No validation found for `preprocess` method")