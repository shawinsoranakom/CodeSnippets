def _test_EmbeddingBag_vs_Embedding(
        self,
        N,
        D,
        B,
        L,
        max_norm=None,
        mode="mean",
        device="cpu",
        wdtype=torch.float,
        dtype=torch.long,
        test_per_sample_weights=False,
        trainable_per_sample_weights=False,
        sparse=False,
        test_backward=True,
        backward_prec=None,
    ):
        es = nn.EmbeddingBag(N, D, mode=mode, sparse=sparse, max_norm=max_norm).to(
            device, wdtype
        )
        e = nn.Embedding(N, D, max_norm=max_norm).to(device, wdtype)
        e.weight.data.copy_(es.weight)
        input = torch.randint(N, (B, L), device=device, dtype=dtype)
        offsets = torch.arange(0, B, device=device, dtype=dtype).mul_(L)
        grad_output = torch.rand(B, D, device=device, dtype=wdtype)

        if test_per_sample_weights:
            # To prevent large gradients, weights should sum to 1 for each bag
            per_sample_weights = torch.randn(B, L, device=device, dtype=wdtype).softmax(
                dim=-1
            )
            per_sample_weights_reference = per_sample_weights.clone().requires_grad_(
                trainable_per_sample_weights
            )
            per_sample_weights.requires_grad_(trainable_per_sample_weights)
            output = es(input.view(-1), offsets, per_sample_weights.view(-1))
        else:
            output = es(input.view(-1), offsets)
            per_sample_weights = None
            per_sample_weights_reference = None

        if mode == "sum":
            if test_per_sample_weights:
                ref_output = (
                    e(input) * per_sample_weights_reference.unsqueeze(-1)
                ).sum(1)
            else:
                ref_output = e(input).sum(1)
        elif mode == "mean":
            if test_per_sample_weights:
                raise AssertionError(
                    "test_per_sample_weights must be False for mean mode"
                )
            ref_output = e(input).mean(1)
        elif mode == "max":
            if test_per_sample_weights:
                raise AssertionError(
                    "test_per_sample_weights must be False for max mode"
                )
            ref_output = e(input).max(1)[0]

        self.assertEqual(output, ref_output, atol=dtype2prec_DONTUSE[wdtype], rtol=0)

        if not test_backward:
            return

        output.backward(grad_output)
        ref_output.backward(grad_output)
        es_weight_grad = es.weight.grad
        if sparse:
            es_weight_grad = es.weight.grad.to_dense()

        # We have more floating point error here because we are dealing with larger numbers
        if backward_prec is None:
            needed_prec = dtype2prec_DONTUSE[wdtype] * 5
            rtol = 0.02 if wdtype == torch.half else 0
        else:
            needed_prec = backward_prec
            rtol = 0

        self.assertEqual(es_weight_grad, e.weight.grad, atol=needed_prec, rtol=rtol)

        if test_per_sample_weights and trainable_per_sample_weights:
            self.assertEqual(
                per_sample_weights.grad,
                per_sample_weights_reference.grad,
                atol=dtype2prec_DONTUSE[wdtype],
                rtol=0,
            )