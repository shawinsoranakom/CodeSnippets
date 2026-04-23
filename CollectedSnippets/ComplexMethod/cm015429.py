def test_all_reduce_coalesced(self) -> None:
        self._init_process_group()

        inputs = [
            torch.full((i, i), float(self.rank * i), device=self.device)
            for i in range(10)
        ]
        outputs = torch.ops._c10d_functional.all_reduce_coalesced(
            inputs,
            "avg",
            "default",
        )
        for i, (output, input) in enumerate(zip(outputs, inputs)):
            output = torch.ops._c10d_functional.wait_tensor(output)
            if id(output) == id(input):
                raise AssertionError("Expected output to be different from input")
            expected = sum(self.ranks) / self.world_size * i
            if not output.eq(expected).all():
                raise AssertionError(f"Expected output to equal {expected}")

        # Test Python API and AsyncCollectiveTensor
        outputs = all_reduce_coalesced(
            inputs,
            "avg",
            "default",
        )
        for i, (output, input) in enumerate(zip(outputs, inputs)):
            if output.completed:
                raise AssertionError("Expected output.completed to be False")
            expected = sum(self.ranks) / self.world_size * i
            if not output.eq(expected).all():
                raise AssertionError(f"Expected output to equal {expected}")
            if not output.completed:
                raise AssertionError(
                    "Expected output.completed to be True after access"
                )