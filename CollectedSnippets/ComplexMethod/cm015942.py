def test_embedding_bag_device(self, device, dtypes):
        if IS_JETSON and torch.bfloat16 in dtypes and device == "cpu":
            self.skipTest("bfloat16 not supported with Jetson cpu")
        if dtypes[2] == torch.float64 and "xpu" in device:
            self.skipTest("https://github.com/intel/torch-xpu-ops/issues/2295")
        with set_default_dtype(torch.double):
            self._test_EmbeddingBag(
                device,
                "sum",
                False,
                wdtype=dtypes[2],
                dtype=dtypes[0],
                odtype=dtypes[1],
            )
            self._test_EmbeddingBag(
                device,
                "mean",
                False,
                wdtype=dtypes[2],
                dtype=dtypes[0],
                odtype=dtypes[1],
            )
            self._test_EmbeddingBag(
                device,
                "max",
                False,
                wdtype=dtypes[2],
                dtype=dtypes[0],
                odtype=dtypes[1],
            )

            test_backward = False
            if self.device_type != "cpu":
                # see 'todo' in test_embedding_bag.
                test_backward = dtypes[2] is not torch.float16
            else:
                # TODO: figure out why precision on sparse embeddings isn't the
                # same as for dense.
                test_backward = (
                    dtypes[2] is not torch.float and dtypes[2] is not torch.float16
                )

            self._test_EmbeddingBag(
                device,
                "sum",
                True,
                wdtype=dtypes[2],
                dtype=dtypes[0],
                odtype=dtypes[1],
                test_backward=test_backward,
            )
            self._test_EmbeddingBag(
                device,
                "mean",
                True,
                wdtype=dtypes[2],
                dtype=dtypes[0],
                odtype=dtypes[1],
                test_backward=test_backward,
            )