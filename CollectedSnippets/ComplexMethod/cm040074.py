def test_basics_with_flash_attention(self):
        enable_flash_attention()
        init_kwargs = {
            "num_query_heads": 2,
            "num_key_value_heads": 2,
            "head_dim": 8,
            "dtype": "float16",
        }
        input_shape = {
            "query_shape": (2, 8, 16),
            "value_shape": (2, 4, 16),
        }
        expected_output_shape = (2, 8, 16)
        if backend.backend() == "torch":
            try:
                self.run_layer_test(
                    layers.GroupedQueryAttention,
                    init_kwargs=init_kwargs,
                    input_shape=input_shape,
                    expected_output_shape=expected_output_shape,
                    expected_num_trainable_weights=8,
                    expected_num_non_trainable_weights=0,
                    expected_num_seed_generators=0,
                    expected_num_losses=0,
                    supports_masking=True,
                    run_training_check=False,
                )
            except ImportError as e:
                if "Flash attention is not supported" in str(e.args[0]):
                    self.assertTrue(
                        (
                            "Flash attention is not supported in your current "
                            "PyTorch version."
                        )
                        in str(e.args[0])
                    )
            except RuntimeError as e:
                if (
                    "Flash attention is not supported with the provided inputs"
                    in str(e.args[0])
                ):
                    self.assertTrue(
                        (
                            "Flash attention is not supported with the "
                            "provided inputs"
                        )
                        in str(e.args[0])
                    )
        elif backend.backend() == "jax":
            try:
                self.run_layer_test(
                    layers.GroupedQueryAttention,
                    init_kwargs=init_kwargs,
                    input_shape=input_shape,
                    expected_output_shape=expected_output_shape,
                    expected_num_trainable_weights=8,
                    expected_num_non_trainable_weights=0,
                    expected_num_seed_generators=0,
                    expected_num_losses=0,
                    supports_masking=True,
                    run_training_check=False,
                )
            except ImportError as e:
                if "Flash attention is not supported" in str(e.args[0]):
                    self.assertTrue(
                        (
                            "Flash attention is not supported in your current "
                            "JAX version."
                        )
                        in str(e.args[0])
                    )
            except RuntimeError as e:
                if "cuDNN" in str(e.args[0]):
                    self.assertTrue("cuDNN is not detected." in str(e.args[0]))
                elif "Require at least" in str(e.args[0]):
                    self.assertTrue(
                        "Require at least Ampere arch to run" in str(e.args[0])
                    )
                elif "Flash attention" in str(e.args[0]):
                    self.assertTrue(
                        (
                            "Flash attention is not supported in your current "
                            "JAX version."
                        )
                        in str(e.args[0])
                    )