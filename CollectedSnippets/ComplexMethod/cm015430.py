def test_all_gather_into_tensor_single(self) -> None:
        self._init_process_group()

        input = torch.full((10, 10), float(self.rank), device=self.device)
        output = torch.ops._c10d_functional.all_gather_into_tensor(
            input,
            self.world_size,
            "default",
        )
        output = torch.ops._c10d_functional.wait_tensor(output)
        expect = torch.cat(
            [
                torch.full((10, 10), float(rank), device=self.device)
                for rank in self.ranks
            ]
        )
        if not torch.allclose(output, expect):
            raise AssertionError("Expected output to be close to expect")
        if not output.eq(expect).all():
            raise AssertionError("Expected output to equal expect")

        # Test out-variant of all_gather_into_tensor
        output = torch.empty(expect.shape, device=self.device)
        output = torch.ops._c10d_functional.all_gather_into_tensor_out(
            input,
            self.world_size,
            "default",
            out=output,
        )
        output = torch.ops._c10d_functional.wait_tensor(output)
        if not torch.allclose(output, expect):
            raise AssertionError("Expected output to be close to expect")
        if not output.eq(expect).all():
            raise AssertionError("Expected output to equal expect")

        # Test Python API and AsyncCollectiveTensor
        output = all_gather_tensor(
            input,
            0,
            "default",
        )
        if not isinstance(output, AsyncCollectiveTensor):
            raise AssertionError(f"Expected AsyncCollectiveTensor, got {type(output)}")
        if output.completed:
            raise AssertionError("Expected output.completed to be False")
        if not output.eq(expect).all():
            raise AssertionError("Expected output to equal expect")
        if not output.completed:
            raise AssertionError("Expected output.completed to be True after access")