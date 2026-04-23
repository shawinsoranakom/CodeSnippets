def test_can_load_ignoring_mismatched_shapes(self):
        if not self.test_mismatched_shapes:
            self.skipTest(reason="test_mismatched_shapes is set to False")

        # Set seed for deterministic weight initialization
        set_seed(42)

        config, inputs_dict = self.model_tester.prepare_config_and_inputs_for_common()

        configs_no_init = _config_zero_init(config)
        configs_no_init.num_labels = 3

        for model_class in self.all_model_classes:
            mappings = [
                MODEL_FOR_SEQUENCE_CLASSIFICATION_MAPPING_NAMES,
                MODEL_FOR_IMAGE_CLASSIFICATION_MAPPING_NAMES,
                MODEL_FOR_AUDIO_CLASSIFICATION_MAPPING_NAMES,
                MODEL_FOR_VIDEO_CLASSIFICATION_MAPPING_NAMES,
            ]
            is_classication_model = any(model_class.__name__ in get_values(mapping) for mapping in mappings)

            if not is_classication_model:
                continue

            with self.subTest(msg=f"Testing {model_class}"):
                with tempfile.TemporaryDirectory() as tmp_dir:
                    model = model_class(configs_no_init)
                    model.save_pretrained(tmp_dir)

                    # Fails when we don't set ignore_mismatched_sizes=True
                    with self.assertRaises(RuntimeError):
                        new_model = model_class.from_pretrained(tmp_dir, num_labels=42)

                    logger = logging.get_logger("transformers.modeling_utils")

                    with CaptureLogger(logger) as cl:
                        new_model = model_class.from_pretrained(tmp_dir, num_labels=42, ignore_mismatched_sizes=True)
                    self.assertIn("Reinit due to size mismatch", cl.out)

                    # Find the name of the module with the mismatched size
                    top_linear_modules = [
                        (name, module) for name, module in new_model.named_children() if isinstance(module, nn.Linear)
                    ]
                    # Some old model have the Linear classification layer inside a ClassificationHead module or nn.Sequential
                    if len(top_linear_modules) == 0:
                        # ClassificationHead case
                        if any(
                            module.__class__.__name__.endswith("ClassificationHead") for module in new_model.children()
                        ):
                            head_name, head_module = next(
                                (name, module)
                                for name, module in new_model.named_children()
                                if module.__class__.__name__.endswith("ClassificationHead")
                            )
                        # nn.Sequential case
                        elif any(isinstance(module, nn.Sequential) for module in new_model.children()):
                            head_name, head_module = next(
                                (name, module)
                                for name, module in new_model.named_children()
                                if isinstance(module, nn.Sequential)
                            )
                        # Unknown at this point -> skip (only xlm, perceiver, levit, flaubert, audio_spectrogram_transformer as of 23/09/2025)
                        else:
                            self.skipTest("Could not locate the classification Linear layer.")
                        top_linear_modules = [
                            (f"{head_name}.{name}", module)
                            for name, module in head_module.named_children()
                            if isinstance(module, nn.Linear)
                        ]
                    # Usually we have only 1, but swiftformer and deit have 2 Linear layers using `num_labels`
                    mismatched_modules = [name for name, module in top_linear_modules if module.out_features == 42]
                    old = dict(model.named_parameters())
                    new = dict(new_model.named_parameters())
                    assert not set(old.keys()) - set(new.keys())
                    for k1 in new.keys():
                        k2 = k1
                        v1 = old[k1]
                        v2 = new[k2]
                        # Each param except the mismatched ones must be exactly similar
                        if not any(k1.startswith(mismatched_module) for mismatched_module in mismatched_modules):
                            torch.testing.assert_close(v1, v2, msg=f"{k1} and  {k2} do not match: {v1} != {v2}")
                        # Check that the dims are indeed mismatched between old and new models
                        else:
                            # The old model should have `num_labels=3` (here it's the first dim of shape, as Linear layers
                            # are transposed)
                            self.assertEqual(v2.shape[0], 42)
                            # Make sure the mean of the new Linear layer is correctly centered around 0 (we cannot use
                            # a lower value for the check as some models hardcode a std of 0.02 instead of using the
                            # config, which we set very small with `config_no_init`)
                            self.assertLessEqual(v1.data.mean().item(), 1e-1, f"Issue with {k1}")