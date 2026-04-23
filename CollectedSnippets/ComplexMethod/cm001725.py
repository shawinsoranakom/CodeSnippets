def test_override_instance_attributes_does_not_affect_other_instances(self):
        if self.fast_video_processing_class is None:
            self.skipTest(
                "Only testing fast video processor, as most slow processors break this test and are to be deprecated"
            )

        video_processing_class = self.fast_video_processing_class
        video_processor_1 = video_processing_class()
        video_processor_2 = video_processing_class()
        if not (hasattr(video_processor_1, "size") and isinstance(video_processor_1.size, dict)) or not (
            hasattr(video_processor_1, "image_mean") and isinstance(video_processor_1.image_mean, list)
        ):
            self.skipTest(
                reason="Skipping test as the image processor does not have dict size or list image_mean attributes"
            )

        original_size_2 = deepcopy(video_processor_2.size)
        for key in video_processor_1.size:
            video_processor_1.size[key] = -1
        modified_copied_size_1 = deepcopy(video_processor_1.size)

        original_image_mean_2 = deepcopy(video_processor_2.image_mean)
        video_processor_1.image_mean[0] = -1
        modified_copied_image_mean_1 = deepcopy(video_processor_1.image_mean)

        # check that the original attributes of the second instance are not affected
        self.assertEqual(video_processor_2.size, original_size_2)
        self.assertEqual(video_processor_2.image_mean, original_image_mean_2)

        for key in video_processor_2.size:
            video_processor_2.size[key] = -2
        video_processor_2.image_mean[0] = -2

        # check that the modified attributes of the first instance are not affected by the second instance
        self.assertEqual(video_processor_1.size, modified_copied_size_1)
        self.assertEqual(video_processor_1.image_mean, modified_copied_image_mean_1)