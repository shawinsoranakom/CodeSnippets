def test_dot_product_attention(
        self, bias, scale, mask_and_is_causal, flash_attention
    ):
        mask, is_causal = mask_and_is_causal
        query_shape = (2, 3, 4, 8)
        key_shape = (2, 3, 4, 8)
        bias_shape = (2, 4, 3, 3)
        query = np.arange(math.prod(query_shape), dtype=float).reshape(
            query_shape
        )
        key = np.arange(math.prod(key_shape), dtype=float).reshape(key_shape)
        value = np.arange(math.prod(key_shape), dtype=float).reshape(key_shape)
        if mask is not None:
            mask = np.tril(np.ones((3, 3))).astype("bool")
            mask = mask[None, None, ...]
            mask = np.tile(mask, (2, 4, 1, 1))
        if bias is not None:
            if backend.backend() == "openvino":
                self.skipTest(
                    "openvino does not support `bias` with "
                    "`dot_product_attention`"
                )
            if backend.backend() == "torch" and mask is not None:
                self.skipTest(
                    "torch does not support `mask` and `bias` with "
                    "`dot_product_attention`"
                )
            bias = np.arange(math.prod(bias_shape), dtype=float).reshape(
                bias_shape
            )

        if flash_attention:
            if backend.backend() in ("tensorflow", "numpy", "openvino"):
                self.skipTest(
                    "Flash attention is not supported in tensorflow, numpy, "
                    "and openvino backends."
                )
            elif backend.backend() == "torch":
                import torch

                if bias is not None:
                    self.skipTest(
                        "Flash attention doesn't support `bias` in torch "
                        "backend."
                    )
                if mask is not None:
                    self.skipTest(
                        "Flash attention doesn't support `mask=None` in torch "
                        "backend."
                    )
                if not torch.cuda.is_available():
                    self.skipTest(
                        "Flash attention must be run on CUDA in torch backend."
                    )
                cuda_compute_capability = tuple(
                    int(x) for x in torch.cuda.get_device_capability()
                )
                if cuda_compute_capability < (8, 0):
                    self.skipTest(
                        "Flash attention must be run on CUDA compute "
                        "capability >= 8.0 in torch backend."
                    )
            elif backend.backend() == "jax":
                import jax
                from jax._src import xla_bridge

                if "cuda" not in xla_bridge.get_backend().platform_version:
                    self.skipTest(
                        "Flash attention must be run on CUDA in jax backend."
                    )
                d, *_ = jax.local_devices(backend="gpu")
                cuda_compute_capability = tuple(
                    int(x) for x in d.compute_capability.split(".")
                )
                if cuda_compute_capability < (8, 0):
                    self.skipTest(
                        "Flash attention must be run on CUDA compute "
                        "capability >= 8.0 in jax backend."
                    )

            # Flash attention only supports float16 and bfloat16. We multiply
            # 0.1 to avoid overflow.
            query = (query * 0.1).astype("float16")
            key = (key * 0.1).astype("float16")
            value = (value * 0.1).astype("float16")
            if bias is not None:
                bias = (bias * 0.1).astype("float16")

        outputs = knn.dot_product_attention(
            query,
            key,
            value,
            bias=bias,
            mask=mask,
            scale=scale,
            is_causal=is_causal,
            flash_attention=flash_attention,
        )

        expected = _dot_product_attention(
            query,
            key,
            value,
            bias=bias,
            mask=mask,
            scale=scale,
            is_causal=is_causal,
        )
        self.assertAllClose(
            outputs, expected, atol=1e-3 if flash_attention else 1e-6
        )