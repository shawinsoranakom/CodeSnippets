def test_slow_fast_equivalence_batched(self):
        """Test batched equivalence across backends including segmentation maps."""
        if len(self.image_processing_classes) < 2:
            self.skipTest(reason="Skipping backends equivalence test as there are less than 2 backends")

        if hasattr(self.image_processor_tester, "do_center_crop") and self.image_processor_tester.do_center_crop:
            self.skipTest(
                reason="Skipping as do_center_crop is True and center_crop functions are not equivalent for fast and slow processors"
            )

        dummy_images, dummy_maps = prepare_semantic_batch_inputs()

        encodings = {}
        for backend_name, image_processing_class in self.image_processing_classes.items():
            image_processor = image_processing_class(**self.image_processor_dict)
            encodings[backend_name] = image_processor(dummy_images, segmentation_maps=dummy_maps, return_tensors="pt")

        backend_names = list(encodings.keys())
        reference_backend = backend_names[0]
        reference_pixel_values = encodings[reference_backend].pixel_values
        reference_mask_labels = encodings[reference_backend].mask_labels
        reference_class_labels = encodings[reference_backend].class_labels

        for backend_name in backend_names[1:]:
            self._assert_tensors_equivalence(reference_pixel_values, encodings[backend_name].pixel_values)
            for mask_label_ref, mask_label_other in zip(reference_mask_labels, encodings[backend_name].mask_labels):
                self._assert_tensors_equivalence(mask_label_ref, mask_label_other)
            for class_label_ref, class_label_other in zip(
                reference_class_labels, encodings[backend_name].class_labels
            ):
                self._assert_tensors_equivalence(class_label_ref.float(), class_label_other.float())