def test_save_load_backends_auto(self):
        "Test that we can load image processors with different backends from each other using AutoImageProcessor."
        if len(self.image_processing_classes) < 2:
            self.skipTest("Skipping backend save/load test as there are less than 2 backends")

        image_processor_dict = self.image_processor_tester.prepare_image_processor_dict()
        backend_names = list(self.image_processing_classes.keys())

        # Test cross-loading between all backend pairs using AutoImageProcessor
        for backend1 in backend_names:
            processor1 = self.image_processing_classes[backend1](**image_processor_dict)

            for backend2 in backend_names:
                if backend1 == backend2:
                    continue

                # Load backend2 processor from backend1 saved one using AutoImageProcessor
                with tempfile.TemporaryDirectory() as tmpdirname:
                    processor1.save_pretrained(tmpdirname)
                    processor2 = AutoImageProcessor.from_pretrained(tmpdirname, backend=backend2)

                # Compare dictionaries (allowing for backend-specific differences)
                dict1 = processor1.to_dict()
                dict2 = processor2.to_dict()
                difference = {
                    key: dict1.get(key) if key in dict1 else dict2.get(key) for key in set(dict1) ^ set(dict2)
                }
                dict1_common = {key: dict1[key] for key in set(dict1) & set(dict2)}
                dict2_common = {key: dict2[key] for key in set(dict1) & set(dict2)}
                # check that all additional keys are None, except for `default_to_square` and `data_format` which are backend-specific
                self.assertTrue(
                    all(
                        value is None
                        for key, value in difference.items()
                        if key not in ["default_to_square", "data_format"]
                    ),
                    f"Backends {backend1} and {backend2} differ in unexpected keys: {difference}",
                )
                # check that the remaining keys are the same
                self.assertEqual(
                    dict1_common, dict2_common, f"Backends {backend1} and {backend2} differ in common keys"
                )