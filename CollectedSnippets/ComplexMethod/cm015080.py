def test_big_num_tensors(self, device, dtype, op, use_cuda_graph, w_empty):
        # foreach_max cannot handle empty tensors as max requires an identity
        intersperse_empty_tensors = w_empty and op.name != "_foreach_max"

        N = 4000
        indices_with_empty_tensors = (
            set()
            if not intersperse_empty_tensors
            else {200, 1500, 1501, 2800, 2801, 2802, 3500, 3998}
        )
        tensorlist = [
            make_tensor((2, 3), dtype=dtype, device=device, noncontiguous=False)
            if i not in indices_with_empty_tensors
            else torch.empty(0, dtype=dtype, device=device)
            for i in range(N)
        ]
        fn, ref_fn, *_ = self._get_funcs(op)

        import math

        if op.name == "_foreach_norm":
            ords = [0, 1, 2]
            if not intersperse_empty_tensors:
                # inf norm over an empty tensor is not defined by vector norm as it expects an identity
                ords.append(math.inf)
        else:
            ords = [None]

        for ord in ords:
            kwargs = {"ord": ord} if ord else {}
            if not use_cuda_graph:
                actual = fn(
                    inputs=[tensorlist],
                    is_cuda=True,
                    expect_fastpath=True,
                    zero_size=False,
                    **kwargs,
                )
            else:
                # When using CUDA graphs and the tensor metadata doesn't fit in
                # the static kernel argument space, multi_tensor_apply creates
                # the launch arguments once, uses cudaUserObject_t to tie its
                # lifetime to the graph, and reuses it throughout replays. This
                # test verifies multi_tensor_apply's behavior in the scenario.
                g = torch.cuda.CUDAGraph()
                with torch.cuda.graph(g):
                    actual = fn.func(tensorlist, **kwargs)
                g.replay()
            expect = ref_fn(inputs=[tensorlist], **kwargs)

            self.assertEqual(expect, actual, equal_nan=True)