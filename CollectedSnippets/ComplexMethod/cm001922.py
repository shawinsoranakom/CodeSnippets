def test_backends_equivalence_batched(self):
        """Override to also compare pixel_attention_mask, rows, and cols (return_row_col_info=True)."""
        if len(self.image_processing_classes) < 2:
            self.skipTest(reason="Skipping backends equivalence test as there are less than 2 backends")

        if hasattr(self.image_processor_tester, "do_center_crop") and self.image_processor_tester.do_center_crop:
            self.skipTest(
                reason="Skipping as do_center_crop is True and center_crop functions are not equivalent for fast and slow processors"
            )

        dummy_images = self.image_processor_tester.prepare_image_inputs(
            equal_resolution=False, num_images=5, torchify=True
        )
        # pop some images to have non homogenous batches:
        indices_to_pop = [i if np.random.random() < 0.5 else None for i in range(len(dummy_images))]
        for i in indices_to_pop:
            if i is not None:
                dummy_images[i].pop()

        encodings = {}
        for backend_name, image_processing_class in self.image_processing_classes.items():
            image_processor = image_processing_class(**self.image_processor_dict, resample=PILImageResampling.BICUBIC)
            encodings[backend_name] = image_processor(dummy_images, return_tensors="pt", return_row_col_info=True)

        backend_names = list(encodings.keys())
        reference_backend = backend_names[0]
        reference = encodings[reference_backend]
        for backend_name in backend_names[1:]:
            encoding = encodings[backend_name]
            self._assert_tensors_equivalence(reference.pixel_values, encoding.pixel_values, atol=3e-1)
            self._assert_tensors_equivalence(
                reference.pixel_attention_mask.float(), encoding.pixel_attention_mask.float()
            )
            self.assertEqual(reference.rows, encoding.rows)
            self.assertEqual(reference.cols, encoding.cols)