def _test_gather(self, dim):
        if not TEST_MULTIGPU:
            raise unittest.SkipTest("only one GPU detected")
        x = torch.randn(2, 5, device=0)
        y = torch.randn(2, 5, device=1)
        expected_size = list(x.size())
        expected_size[dim] += y.size(dim)
        expected_size = torch.Size(expected_size)

        destinations = [None, torch.device("cuda:0"), torch.device("cpu")]
        if torch.cuda.device_count() > 2:
            destinations.append(torch.device("cuda:2"))
        with torch.cuda.device(1):
            for destination in destinations:
                if destination is None:
                    expected_device = torch.device("cuda", torch.cuda.current_device())
                else:
                    expected_device = destination
                for use_out in [True, False]:
                    if use_out:
                        out = torch.empty(expected_size, device=expected_device)
                        result = comm.gather((x, y), dim, out=out)
                        self.assertIs(out, result)
                    else:
                        result = comm.gather((x, y), dim, destination=destination)

                    self.assertEqual(result.device, expected_device)
                    self.assertEqual(result.size(), expected_size)

                    index = [slice(None, None), slice(None, None)]
                    index[dim] = slice(0, x.size(dim))
                    self.assertEqual(result[tuple(index)], x)
                    index[dim] = slice(x.size(dim), x.size(dim) + y.size(dim))
                    self.assertEqual(result[tuple(index)], y)

        # test error msg
        with self.assertRaisesRegex(
            RuntimeError, r"'destination' must not be specified"
        ):
            comm.gather(
                (x, y),
                dim,
                destination="cpu",
                out=torch.empty(expected_size, device="cpu"),
            )
        with self.assertRaisesRegex(
            RuntimeError, r"Expected at least one tensor to gather from"
        ):
            comm.gather(())
        with self.assertRaisesRegex(
            RuntimeError, r"Expected all input tensors to be CUDA tensors, "
        ):
            comm.gather((x.cpu(), y))
        with self.assertRaisesRegex(
            RuntimeError,
            r"Expected all input tensors to have the same number of dimensions",
        ):
            comm.gather((x, y.unsqueeze(0)))
        with self.assertRaisesRegex(
            RuntimeError, r"Input tensor at index 1 has invalid shape"
        ):
            if dim in [0, -2]:
                comm.gather((x, y[:, 1:]), dim=dim)
            elif dim in [1, -1]:
                comm.gather((x, y[1:, :]), dim=dim)