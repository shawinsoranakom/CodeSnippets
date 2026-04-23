def _test_EmbeddingBag(
        self,
        device,
        mode,
        sparse,
        wdtype=torch.double,
        dtype=torch.long,
        odtype=torch.long,
        test_backward=True,
    ):
        # check a known test example
        es = nn.EmbeddingBag(5, 2, mode=mode, sparse=sparse).to(device, wdtype)
        es.weight.data.copy_(
            torch.arange(1, 11, device=device).view_as(es.weight).to(wdtype)
        )
        input = torch.tensor([3, 1, 1, 1, 4, 0], device=device, dtype=dtype)
        offsets = torch.tensor([0, 0, 3, 3, 6], device=device, dtype=odtype)

        grad_output = torch.tensor([1, 2, 3, 4], device=device, dtype=wdtype).view(2, 2)
        grad_output_with_empty = torch.tensor(
            [99, 99, 1, 2, 99, 99, 3, 4, 99, 99], device=device, dtype=wdtype
        ).view(5, 2)

        if mode == "sum" or mode == "mean":
            denominator = 1 if mode == "sum" else 3
            expected_output = (
                torch.tensor([[13, 16], [13, 16]], device=device, dtype=wdtype)
                / denominator
            )

            expected_output_with_empty = (
                torch.tensor(
                    [[0, 0], [13, 16], [0, 0], [13, 16], [0, 0]],
                    device=device,
                    dtype=wdtype,
                )
                / denominator
            )

            expected_grad_weight = (
                torch.tensor(
                    [[3, 4], [5, 8], [0, 0], [1, 2], [3, 4]],
                    device=device,
                    dtype=wdtype,
                )
                / denominator
            )
        elif mode == "max":
            expected_output = torch.tensor(
                [[7, 8], [9, 10]], device=device, dtype=wdtype
            )

            expected_output_with_empty = torch.tensor(
                [[0, 0], [7, 8], [0, 0], [9, 10], [0, 0]], device=device, dtype=wdtype
            )

            expected_grad_weight = torch.tensor(
                [[0, 0], [0, 0], [0, 0], [1, 2], [3, 4]], device=device, dtype=wdtype
            )
        output = es(input, offsets)
        output.backward(grad_output_with_empty)

        es_weight_grad = es.weight.grad
        if sparse:
            es_weight_grad = es.weight.grad.to_dense()
        self.assertEqual(output, expected_output_with_empty)
        self.assertEqual(
            es_weight_grad,
            expected_grad_weight,
            atol=dtype2prec_DONTUSE[wdtype],
            rtol=0,
        )

        # check same example except as 2D (2 x 3)
        input = input.view(2, -1)
        es.zero_grad()
        output = es(input)
        output.backward(grad_output)

        es_weight_grad = es.weight.grad
        if sparse:
            es_weight_grad = es.weight.grad.to_dense()
        self.assertEqual(output, expected_output)
        self.assertEqual(
            es_weight_grad,
            expected_grad_weight,
            atol=dtype2prec_DONTUSE[wdtype],
            rtol=0,
        )

        # test all empty bags
        es.zero_grad()
        inputs = torch.tensor([], dtype=dtype, device=device)
        offsets = torch.tensor([0, 0, 0, 0], dtype=odtype, device=device)
        es(inputs, offsets).sum().backward()
        dense_grad = es.weight.grad
        if dense_grad.is_sparse:
            dense_grad = dense_grad.to_dense()
        self.assertEqual(dense_grad, torch.zeros_like(es.weight))

        # now compare EmbeddingBag vs Embedding + Sum/Mean, for constant bag length
        N, D, B, L = (
            random.randint(1, 100),
            random.randint(1, 100),
            random.randint(1, 50),
            random.randint(1, 50),
        )
        kwargs = dict(
            mode=mode,
            sparse=sparse,
            device=device,
            wdtype=wdtype,
            dtype=dtype,
            test_backward=test_backward,
        )
        self._test_EmbeddingBag_vs_Embedding(N, D, B, L, **kwargs)
        for max_norm in (None, 3):
            for p in itertools.product([1, 2], repeat=4):
                self._test_EmbeddingBag_vs_Embedding(*p, max_norm=max_norm, **kwargs)

        # check that giving illegal input combos raises error
        es = nn.EmbeddingBag(10, 20, mode=mode, sparse=sparse)
        input = torch.ones(3, 4, dtype=dtype)
        offset = torch.arange(0, 3, dtype=odtype)
        torch._dynamo.disable(self.assertRaises)(ValueError, lambda: es(input, offset))
        torch._dynamo.disable(self.assertRaises)(ValueError, lambda: es(input.view(-1)))
        offset[0] = 1
        if self.device_type == "cpu":
            torch._dynamo.disable(self.assertRaises)(
                RuntimeError, lambda: es(input.view(-1), offset)
            )
            offset[0] = 0
            offset[-1] = 100
            torch._dynamo.disable(self.assertRaises)(
                RuntimeError, lambda: es(input.view(-1), offset)
            )