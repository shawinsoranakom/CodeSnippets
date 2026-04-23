def _test_scatter(self, input, chunk_sizes=None, dim=0):
        if not TEST_MULTIGPU:
            raise unittest.SkipTest("only one GPU detected")
        if chunk_sizes is None:
            ref_chunk_sizes = tuple(repeat(input.size(dim) // 2, 2))
        else:
            ref_chunk_sizes = chunk_sizes

        # test regular
        result = comm.scatter(input, (0, 1), chunk_sizes, dim)
        self.assertEqual(len(result), 2)
        chunk_start = 0
        for i, r in enumerate(result):
            chunk_end = chunk_start + ref_chunk_sizes[i]
            index = [slice(None, None) for _ in range(input.dim())]
            index[dim] = slice(chunk_start, chunk_end)
            self.assertEqual(r, input[tuple(index)], atol=0, rtol=0)
            chunk_start = chunk_end
            if r.device == input.device:
                self.assertEqual(
                    r.data_ptr(), input.data_ptr()
                )  # for target @ same device, a view should be returned

        # test out
        out = [torch.empty_like(t) for t in result]
        result = comm.scatter(input, dim=dim, out=out)
        self.assertEqual(len(result), 2)
        chunk_start = 0
        for i, r in enumerate(result):
            self.assertIs(r, out[i])
            chunk_end = chunk_start + ref_chunk_sizes[i]
            index = [slice(None, None) for _ in range(input.dim())]
            index[dim] = slice(chunk_start, chunk_end)
            self.assertEqual(r, input[tuple(index)], atol=0, rtol=0)
            chunk_start = chunk_end

        # test error msg
        if chunk_sizes is not None:
            with self.assertRaisesRegex(
                RuntimeError, r"Expected devices and chunk_sizes to be of same length"
            ):
                comm.scatter(
                    input,
                    [0 for _ in range(len(chunk_sizes) + 1)],
                    dim=dim,
                    chunk_sizes=chunk_sizes,
                )
        with self.assertRaisesRegex(RuntimeError, r"'devices' must not be specified"):
            comm.scatter(input, (0, 1), dim=dim, out=out)
        with self.assertRaisesRegex(
            RuntimeError, r"Expected at least one device to scatter to"
        ):
            comm.scatter(input, (), dim=dim)
        with self.assertRaisesRegex(
            RuntimeError, r"Expected at least one output tensor to scatter to"
        ):
            comm.scatter(input, dim=dim, out=[])
        with self.assertRaisesRegex(
            RuntimeError,
            r"Expected all output tensors to be CUDA tensors, but output tensor at index 0",
        ):
            comm.scatter(input, dim=dim, out=([out[0].cpu()] + out[1:]))
        with self.assertRaisesRegex(
            RuntimeError, r"Output tensor at index 0 has incorrect shape"
        ):
            comm.scatter(input, dim=dim, out=([out[0].unsqueeze(0)] + out[1:]))
        with self.assertRaisesRegex(
            RuntimeError,
            r"Total size for output tensors along scatter dim \d+ does not match",
        ):
            index = [slice(None, None) for _ in range(input.dim())]
            index[dim] = slice(1, None)
            comm.scatter(input, dim=dim, out=([out[0][tuple(index)]] + out[1:]))