def test_override_instance_attributes_does_not_affect_other_instances(self):
        # Test with all available backends
        for backend_name, image_processing_class in self.image_processing_classes.items():
            with self.subTest(backend=backend_name):
                image_processor_1 = image_processing_class()
                image_processor_2 = image_processing_class()
                if not (hasattr(image_processor_1, "size") and isinstance(image_processor_1.size, dict)) or not (
                    hasattr(image_processor_1, "image_mean") and isinstance(image_processor_1.image_mean, list)
                ):
                    self.skipTest(
                        reason="Skipping test as the image processor does not have dict size or list image_mean attributes"
                    )

                original_size_2 = deepcopy(image_processor_2.size)
                for key in image_processor_1.size:
                    image_processor_1.size[key] = -1
                modified_copied_size_1 = deepcopy(image_processor_1.size)

                original_image_mean_2 = deepcopy(image_processor_2.image_mean)
                image_processor_1.image_mean[0] = -1
                modified_copied_image_mean_1 = deepcopy(image_processor_1.image_mean)

                # check that the original attributes of the second instance are not affected
                self.assertEqual(image_processor_2.size, original_size_2)
                self.assertEqual(image_processor_2.image_mean, original_image_mean_2)

                for key in image_processor_2.size:
                    image_processor_2.size[key] = -2
                image_processor_2.image_mean[0] = -2

                # check that the modified attributes of the first instance are not affected by the second instance
                self.assertEqual(image_processor_1.size, modified_copied_size_1)
                self.assertEqual(image_processor_1.image_mean, modified_copied_image_mean_1)