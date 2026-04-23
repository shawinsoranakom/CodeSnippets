def test_reduce_scatter_tensor_coalesced(self) -> None:
        self._init_process_group()

        inputs = [torch.tensor(self.ranks, device=self.device) * i for i in range(10)]
        outputs = torch.ops._c10d_functional.reduce_scatter_tensor_coalesced(
            inputs,
            "avg",
            self.world_size,
            "default",
        )
        for i, output in enumerate(outputs):
            output = torch.ops._c10d_functional.wait_tensor(output)
            expected = self.rank * i
            if not output.eq(expected).all():
                raise AssertionError(f"Expected output to equal {expected}")

        # Test Python API and AsyncCollectiveTensor
        outputs = reduce_scatter_tensor_coalesced(
            inputs,
            "avg",
            [0] * 10,
            "default",
        )
        for i, output in enumerate(outputs):
            if output.completed:
                raise AssertionError("Expected output.completed to be False")
            expected = self.rank * i
            if not output.eq(expected).all():
                raise AssertionError(f"Expected output to equal {expected}")
            if not output.completed:
                raise AssertionError(
                    "Expected output.completed to be True after access"
                )