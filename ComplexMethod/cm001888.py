def test_backends_equivalence_batched(self):
        """Override to also compare pixel_attention_mask across backends."""
        if len(self.image_processing_classes) < 2:
            self.skipTest(reason="Skipping backends equivalence test as there are less than 2 backends")

        dummy_images = self.image_processor_tester.prepare_image_inputs(
            equal_resolution=False, num_images=5, torchify=True
        )
        indices_to_pop = [i if np.random.random() < 0.5 else None for i in range(len(dummy_images))]
        for i in indices_to_pop:
            if i is not None:
                dummy_images[i].pop()

        encodings = {}
        for backend_name, image_processing_class in self.image_processing_classes.items():
            image_processor = image_processing_class(**self.image_processor_dict)
            encodings[backend_name] = image_processor(dummy_images, return_tensors="pt")

        backend_names = list(encodings.keys())
        reference_backend = backend_names[0]
        reference_pixel_values = encodings[reference_backend].pixel_values
        reference_mask = encodings[reference_backend].pixel_attention_mask.float()

        for backend_name in backend_names[1:]:
            self._assert_tensors_equivalence(reference_pixel_values, encodings[backend_name].pixel_values)
            self._assert_tensors_equivalence(reference_mask, encodings[backend_name].pixel_attention_mask.float())