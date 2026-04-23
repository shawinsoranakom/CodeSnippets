def test_model_outputs(self, quantized, model, kernels, attn_impl, mode):
        if torch_device == "cpu":
            if attn_impl == "kernels-community/vllm-flash-attn3":
                self.skipTest("vllm-flash-attn3 is not supported on CPU.")
            if kernels and mode == "train":
                self.skipTest("CPU kernels only support inference.")

        if torch_device == "xpu" and attn_impl == "kernels-community/vllm-flash-attn3":
            self.skipTest("flash attention 3 is not supported on XPU yet.")

        model_id = f"openai/gpt-oss-{model}"
        output_texts = self.load_and_forward(
            model_id,
            attn_impl,
            self.input_text,
            mode=mode,
            use_kernels=kernels,
        )

        # Generate key to look up expected outputs
        key = self.generate_config_key(quantized, model, kernels, attn_impl, mode)

        # Load expected outputs from restructured JSON
        if os.path.exists(RESULTS_PATH):
            with open(RESULTS_PATH, "r") as f:
                expected_results = json.load(f)

            # Check if we have expected results for this configuration
            if key in expected_results:
                expected_outputs = expected_results[key]

                # Compare actual outputs with expected outputs
                self.assertEqual(len(output_texts), len(expected_outputs), f"Output length mismatch for {key}")

                for i, (actual, expected) in enumerate(zip(output_texts, expected_outputs)):
                    actual_stripped = actual.strip()
                    expected_stripped = expected.strip()

                    # Make lengths match by taking minimum length to be resilient to generation differences
                    min_length = min(len(actual_stripped), len(expected_stripped))
                    actual_truncated = actual_stripped[:min_length]
                    expected_truncated = expected_stripped[:min_length]

                    if actual_truncated != expected_truncated:
                        diff = "\n".join(
                            difflib.unified_diff(
                                expected_truncated.splitlines(keepends=True),
                                actual_truncated.splitlines(keepends=True),
                                fromfile=f"expected[{i}]",
                                tofile=f"actual[{i}]",
                                lineterm="",
                            )
                        )
                        self.fail(
                            f"Output mismatch at index {i} for {key}:\n"
                            f"Expected: '{expected_stripped}'\n"
                            f"Actual:   '{actual_stripped}'\n"
                            f"Diff (truncated to min length {min_length}):\n{diff}"
                        )
            else:
                # If no expected results exist, this is a new configuration
                # We could optionally add it to the results file here
                print(f"Warning: No expected results found for configuration: {key}")

        self.assertIsInstance(output_texts, list)
        self.assertTrue(all(isinstance(x, str) for x in output_texts))