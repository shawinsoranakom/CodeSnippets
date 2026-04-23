def _test_broadcast(self, input):
        if not TEST_MULTIGPU:
            raise unittest.SkipTest("only one GPU detected")
        # test regular
        results = comm.broadcast(input, (0, 1))
        for i, t in enumerate(results):
            self.assertEqual(t.get_device(), i)
            self.assertEqual(t, input)
            if (
                input.is_cuda and input.get_device() == i
            ):  # test not copying on same device
                self.assertEqual(t.data_ptr(), input.data_ptr())
        # test out=
        for inplace in [True, False]:
            if inplace:
                outputs = [
                    torch.empty_like(input, device=0),
                    torch.empty_like(input, device=1),
                ]
            else:
                outputs = [input.cuda(0), torch.empty_like(input, device=1)]
            results = comm.broadcast(input, out=outputs)
            for r, o in zip(results, outputs):
                self.assertIs(r, o)
            for i, t in enumerate(results):
                self.assertEqual(t.get_device(), i)
                self.assertEqual(t, input)
        # test error msg
        with self.assertRaisesRegex(
            RuntimeError, r"Exactly one of 'devices' and 'out'"
        ):
            comm.broadcast(input, (0, 1), out=outputs)
        with self.assertRaisesRegex(
            RuntimeError,
            r"Expected all output tensors to be CUDA tensors, but output tensor at index 1",
        ):
            comm.broadcast(input, out=[input.cuda(0), input.cpu()])
        with self.assertRaisesRegex(
            RuntimeError,
            r"Expected all output tensors to have same shape as the source .+ at index 1",
        ):
            comm.broadcast(input, out=[input.cuda(0), input.cuda(1).unsqueeze(0)])