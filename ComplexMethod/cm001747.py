def _test_eager_matches_batched_and_grouped_inference(self, name, dtype):
    if not self.all_model_classes[0]._can_set_experts_implementation():
        self.skipTest(f"{self.all_model_classes[0].__name__} does not support grouped_mm")

    # convert shorthand name to torch.dtype
    if dtype == "fp16":
        dtype = torch.float16
    elif dtype == "bf16":
        dtype = torch.bfloat16
    elif dtype == "fp32":
        dtype = torch.float32

    if not is_torch_fp16_available_on_device(torch_device) and dtype == torch.float16:
        self.skipTest(f"float16 not supported on {torch_device} (on the specific device currently used)")

    if not is_torch_bf16_available_on_device(torch_device) and dtype == torch.bfloat16:
        self.skipTest(
            f"bfloat16 not supported on {torch_device} (on the specific device currently used, e.g. Nvidia T4 GPU)"
        )

    for model_class in self.all_model_classes:
        # Set seed for deterministic test - ensures reproducible model initialization and inputs
        set_seed(42)
        config, inputs_dict = self.model_tester.prepare_config_and_inputs_for_common()
        set_config_for_less_flaky_test(config)
        model = model_class(config).eval().to(torch_device).to(dtype)
        set_model_for_less_flaky_test(model)

        # Reload to find any buffer misalignments after saving/loading
        with tempfile.TemporaryDirectory() as tmpdirname:
            model.save_pretrained(tmpdirname)
            model = model_class.from_pretrained(tmpdirname).eval().to(torch_device).to(dtype)

        with torch.no_grad():
            inputs_dict = {k: v.to(dtype) if torch.is_floating_point(v) else v for k, v in inputs_dict.items()}
            prepared_inputs = self._prepare_for_class(inputs_dict, model_class)

            mock_batched_mm_forward = Mock(wraps=batched_mm_experts_forward)
            mock_grouped_mm_forward = Mock(wraps=grouped_mm_experts_forward)
            with (
                # This is needed because we call the functions through the interface's global mapping
                patch.dict(
                    "transformers.integrations.moe.ALL_EXPERTS_FUNCTIONS._global_mapping",
                    {"batched_mm": mock_batched_mm_forward, "grouped_mm": mock_grouped_mm_forward},
                ),
            ):
                model.set_experts_implementation("eager")
                self.assertEqual(model.config._experts_implementation, "eager")
                outputs_eager = model(**prepared_inputs)
                mock_batched_mm_forward.assert_not_called()
                mock_grouped_mm_forward.assert_not_called()

                mock_batched_mm_forward.reset_mock()
                mock_grouped_mm_forward.reset_mock()

                model.set_experts_implementation("batched_mm")
                self.assertEqual(model.config._experts_implementation, "batched_mm")
                outputs_batched_mm = model(**prepared_inputs)
                mock_grouped_mm_forward.assert_not_called()
                mock_batched_mm_forward.assert_called()

                mock_batched_mm_forward.reset_mock()
                mock_grouped_mm_forward.reset_mock()

                model.set_experts_implementation("grouped_mm")
                self.assertEqual(model.config._experts_implementation, "grouped_mm")
                outputs_grouped_mm = model(**prepared_inputs)
                mock_batched_mm_forward.assert_not_called()
                mock_grouped_mm_forward.assert_called()

                mock_batched_mm_forward.reset_mock()
                mock_grouped_mm_forward.reset_mock()

        # extract output tensors for comparison
        outputs_eager = _get_output_tensors(outputs_eager)
        outputs_batched_mm = _get_output_tensors(outputs_batched_mm)
        outputs_grouped_mm = _get_output_tensors(outputs_grouped_mm)

        # make sure we have collected some tensors from the outputs
        self.assertTrue(outputs_eager, "No outputs from eager implementation")
        self.assertTrue(outputs_batched_mm, "No outputs from batched_mm implementation")
        self.assertTrue(outputs_grouped_mm, "No outputs from grouped_mm implementation")

        # make sure all implementations give numerically close outputs
        torch.testing.assert_close(outputs_eager, outputs_batched_mm, rtol=1e-4, atol=1e-4)
        torch.testing.assert_close(outputs_eager, outputs_grouped_mm, rtol=1e-4, atol=1e-4)