def test_backends_equivalence_batched(self):
        """Override to also compare high_res_pixel_values (variable shape - list of tensors)."""
        if len(self.image_processing_classes) < 2:
            self.skipTest(reason="Skipping backends equivalence test as there are less than 2 backends")

        dummy_images = self.image_processor_tester.prepare_image_inputs(equal_resolution=False, torchify=True)

        encodings = {}
        for backend_name, image_processing_class in self.image_processing_classes.items():
            image_processor = image_processing_class(**self.image_processor_dict)
            encodings[backend_name] = image_processor(dummy_images, return_tensors=None)

        backend_names = list(encodings.keys())
        reference_backend = "pil"
        ref_pixel_values = encodings[reference_backend].pixel_values
        ref_high_res = encodings[reference_backend].high_res_pixel_values

        for backend_name in [backend_name for backend_name in backend_names if backend_name != reference_backend]:
            for i in range(len(ref_pixel_values)):
                self._assert_tensors_equivalence(
                    torch.from_numpy(ref_pixel_values[i]), encodings[backend_name].pixel_values[i]
                )
            for i in range(len(ref_high_res)):
                self._assert_tensors_equivalence(
                    torch.from_numpy(ref_high_res[i]), encodings[backend_name].high_res_pixel_values[i]
                )