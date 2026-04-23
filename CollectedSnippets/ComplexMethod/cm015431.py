def test_all_gather_into_tensor_coalesced(self) -> None:
        self._init_process_group()

        inputs = [
            torch.full((10, 10), float(self.rank * i), device=self.device)
            for i in range(10)
        ]
        outputs = torch.ops._c10d_functional.all_gather_into_tensor_coalesced(
            inputs,
            self.world_size,
            "default",
        )
        expect = [
            torch.cat(
                [
                    torch.full((10, 10), float(rank) * i, device=self.device)
                    for rank in self.ranks
                ]
            )
            for i in range(10)
        ]
        for i, output in enumerate(outputs):
            output = torch.ops._c10d_functional.wait_tensor(output)
            if not output.eq(expect[i]).all():
                raise AssertionError(f"Expected output to equal expect[{i}]")

        # Test Python API and AsyncCollectiveTensor
        outputs = all_gather_into_tensor_coalesced(
            inputs,
            "default",
        )
        for i, output in enumerate(outputs):
            if output.completed:
                raise AssertionError("Expected output.completed to be False")
            if not output.eq(expect[i]).all():
                raise AssertionError(f"Expected output to equal expect[{i}]")
            if not output.completed:
                raise AssertionError(
                    "Expected output.completed to be True after access"
                )