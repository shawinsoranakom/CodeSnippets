def test_flex_attention_logging(self, device):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "flex_attention_configs")

            with patch.dict(
                os.environ, {"TORCHINDUCTOR_FLEX_ATTENTION_LOGGING_FILE": log_file}
            ):
                query = torch.randn(
                    1,
                    2,
                    128,
                    64,
                    device=device,
                    dtype=torch.float16,
                    requires_grad=True,
                )
                key = torch.randn(
                    1,
                    2,
                    128,
                    64,
                    device=device,
                    dtype=torch.float16,
                    requires_grad=True,
                )
                value = torch.randn(
                    1,
                    2,
                    128,
                    64,
                    device=device,
                    dtype=torch.float16,
                    requires_grad=True,
                )

                def score_mod(score, b, h, q_idx, kv_idx):
                    return score * 2

                def causal_mask(b, h, q_idx, kv_idx):
                    return q_idx >= kv_idx

                block_mask = torch.compile(create_block_mask)(
                    causal_mask, 1, 1, 128, 128, device=device
                )

                compiled_flex = torch.compile(
                    flex_attention, mode="max-autotune-no-cudagraphs"
                )

                out = compiled_flex(
                    query=query,
                    key=key,
                    value=value,
                    score_mod=score_mod,
                    block_mask=block_mask,
                )

                out.sum().backward()

                json_file = log_file + ".json"
                self.assertTrue(
                    os.path.exists(json_file), f"Log file {json_file} was not created"
                )

                with open(json_file) as f:
                    log_data = json.load(f)

                self.assertIsInstance(log_data, list)
                self.assertEqual(len(log_data), 2)

                # Check that we have both forward and backward entries
                kernel_types_seen = [entry["kernel_type"] for entry in log_data]
                self.assertIn("forward", kernel_types_seen)
                self.assertIn("backward", kernel_types_seen)

                # Expected values from the test inputs
                expected_query_shape = "[1, 2, 128, 64]"
                expected_key_shape = "[1, 2, 128, 64]"
                expected_value_shape = "[1, 2, 128, 64]"
                expected_B = 1
                expected_Hq = 2
                expected_Hkv = 2
                expected_seq_len_q = 128
                expected_seq_len_kv = 128
                expected_qk_head_dim = 64
                expected_v_head_dim = 64

                for entry in log_data:
                    self.assertIsInstance(entry, dict)
                    # New format has: query_shape, key_shape, value_shape, kernel_type, choices
                    self.assertIn("kernel_type", entry)
                    self.assertIn("choices", entry)
                    self.assertIn("query_shape", entry)
                    self.assertIn("key_shape", entry)
                    self.assertIn("value_shape", entry)

                    # Check shape values
                    self.assertEqual(entry["query_shape"], expected_query_shape)
                    self.assertEqual(entry["key_shape"], expected_key_shape)
                    self.assertEqual(entry["value_shape"], expected_value_shape)

                    kernel_type = entry["kernel_type"]
                    choices = entry["choices"]

                    self.assertIsInstance(choices, list)
                    self.assertGreater(len(choices), 0)

                    for i, choice in enumerate(choices):
                        self.assertIn("type", choice)
                        self.assertIn("time", choice)

                        if choice["type"] == "triton":
                            self.assertIn("num_warps", choice)
                            self.assertIn("num_stages", choice)

                            # Check numerical values in each choice
                            self.assertIn("B", choice)
                            self.assertIn("Hq", choice)
                            self.assertIn("Hkv", choice)
                            self.assertIn("seq_len_q", choice)
                            self.assertIn("seq_len_kv", choice)
                            self.assertIn("qk_head_dim", choice)
                            self.assertIn("v_head_dim", choice)

                            self.assertEqual(choice["B"], expected_B)
                            self.assertEqual(choice["Hq"], expected_Hq)
                            self.assertEqual(choice["Hkv"], expected_Hkv)
                            self.assertEqual(choice["seq_len_q"], expected_seq_len_q)
                            self.assertEqual(choice["seq_len_kv"], expected_seq_len_kv)
                            self.assertEqual(
                                choice["qk_head_dim"], expected_qk_head_dim
                            )
                            self.assertEqual(choice["v_head_dim"], expected_v_head_dim)

                            if kernel_type == "forward":
                                self.assertIn("BLOCK_M", choice)
                                self.assertIn("BLOCK_N", choice)
                                self.assertNotIn("BLOCK_M1", choice)
                            elif kernel_type == "backward":
                                self.assertIn("BLOCK_M1", choice)
                                self.assertIn("BLOCK_N1", choice)
                                self.assertIn("BLOCK_M2", choice)
                                self.assertIn("BLOCK_N2", choice)
                                self.assertNotIn("BLOCK_M", choice)
                                self.assertNotIn("BLOCK_N", choice)

                        if i > 0:
                            self.assertLessEqual(choices[0]["time"], choice["time"])