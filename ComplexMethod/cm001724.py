def test_video_processor_preprocess_arguments(self):
        is_tested = False

        for video_processing_class in self.video_processor_list:
            video_processor = video_processing_class(**self.video_processor_dict)

            # validation done by _valid_processor_keys attribute
            if hasattr(video_processor, "_valid_processor_keys") and hasattr(video_processor, "preprocess"):
                preprocess_parameter_names = inspect.getfullargspec(video_processor.preprocess).args
                preprocess_parameter_names.remove("self")
                preprocess_parameter_names.sort()
                valid_processor_keys = video_processor._valid_processor_keys
                valid_processor_keys.sort()
                self.assertEqual(preprocess_parameter_names, valid_processor_keys)
                is_tested = True

            # validation done by @filter_out_non_signature_kwargs decorator
            if hasattr(video_processor.preprocess, "_filter_out_non_signature_kwargs"):
                if hasattr(self.video_processor_tester, "prepare_video_inputs"):
                    inputs = self.video_processor_tester.prepare_video_inputs()
                elif hasattr(self.video_processor_tester, "prepare_video_inputs"):
                    inputs = self.video_processor_tester.prepare_video_inputs()
                else:
                    self.skipTest(reason="No valid input preparation method found")

                with warnings.catch_warnings(record=True) as raised_warnings:
                    warnings.simplefilter("always")
                    video_processor(inputs, extra_argument=True)

                messages = " ".join([str(w.message) for w in raised_warnings])
                self.assertGreaterEqual(len(raised_warnings), 1)
                self.assertIn("extra_argument", messages)
                is_tested = True

        if not is_tested:
            self.skipTest(reason="No validation found for `preprocess` method")