def test_save_load_pretrained_additional_features(self):
        """
        Tests that additional kwargs passed to from_pretrained are correctly applied to components.
        """
        attributes = self.processor_class.get_attributes()

        if not any(
            attr in ["tokenizer", "image_processor", "feature_extractor", "audio_processor", "video_processor"]
            for attr in attributes
        ):
            self.skipTest("Processor has no tokenizer or image_processor to test additional features")
        additional_kwargs = {}

        has_tokenizer = "tokenizer" in attributes
        if has_tokenizer:
            additional_kwargs["cls_token"] = "(CLS)"
            additional_kwargs["sep_token"] = "(SEP)"

        has_image_processor = "image_processor" in attributes
        if has_image_processor:
            additional_kwargs["do_normalize"] = False
        has_video_processor = "video_processor" in attributes
        if has_video_processor:
            additional_kwargs["do_normalize"] = False

        processor_second = self.processor_class.from_pretrained(self.tmpdirname, **additional_kwargs)
        if has_tokenizer:
            self.assertEqual(processor_second.tokenizer.cls_token, "(CLS)")
            self.assertEqual(processor_second.tokenizer.sep_token, "(SEP)")
        if has_image_processor:
            self.assertEqual(processor_second.image_processor.do_normalize, False)
        if has_video_processor:
            self.assertEqual(processor_second.video_processor.do_normalize, False)