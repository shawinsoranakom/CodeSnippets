def test_embedding_bag_2D_padding_idx(self, device, dtype):
        # Use a Python implementation of embedding_bag with padding_idx support
        # to check torch.nn.functional.embedding_bag correctness
        def embedding_bag_check(indices, weights, mode, sparse, padding_idx):
            if padding_idx is None:
                raise AssertionError("padding_idx must not be None")
            embedding = torch.nn.functional.embedding(
                indices, weights, padding_idx=padding_idx, sparse=sparse
            )

            reduction_dim = indices.dim() - 1

            if mode == "sum" or mode == "mean":
                # We must avoid including elements at padding_idx in the
                # sum/mean, so multiply those elements by 0, and multiply
                # all other elements by 1
                per_sample_weights = indices.ne(padding_idx).to(dtype).unsqueeze(-1)
                res = embedding.mul(per_sample_weights).sum(dim=reduction_dim)

                if mode == "mean":
                    weights_sum = per_sample_weights.sum(dim=reduction_dim)
                    res = res.div(weights_sum)

            elif mode == "max":
                # We must avoid allowing elements at padding_idx to be chosen
                # as the max, so set those elements to negative infinity
                res = embedding.masked_fill(
                    indices.unsqueeze(-1) == padding_idx, -float("inf")
                ).amax(dim=reduction_dim)

            else:
                raise RuntimeError(f"mode '{mode}' is not available")

            # If a row is all padding, set its corresponding result row to 0.
            # This is needed because the above mean and max mode
            # implementations set these elements to nan and -inf, respectively
            if mode in ["mean", "max"]:
                res = res.masked_fill(
                    indices.eq(padding_idx).all(dim=-1).unsqueeze(-1), 0
                )

            return res

        num_features = 3
        num_words = 10
        indices_dim1 = 10

        for mode, sparse, allpad, indices_dim0 in product(
            ["max", "mean", "sum"], [False, True], [False, True], [1, 10]
        ):
            # Max sparse and bfloat16 are not supported
            if mode == "max":
                if sparse or (dtype == torch.bfloat16):
                    continue

            if allpad:
                indices = torch.empty(
                    indices_dim0, indices_dim1, dtype=torch.long, device=device
                ).fill_(1)
            else:
                indices = torch.randint(
                    0, num_words, (indices_dim0, indices_dim1), device=device
                )

                if indices_dim0 > 1:
                    # Fill one row with duplicate index so we can test with a fully
                    # padded row
                    duplicate_row = random.randint(0, indices_dim0 - 1)
                    indices[duplicate_row] = indices[duplicate_row][0]

            for padding_idx in list(set(indices.flatten(0, -1).tolist())):
                weights = torch.randn(
                    num_words,
                    num_features,
                    dtype=dtype,
                    device=device,
                    requires_grad=True,
                )
                weights_check = weights.detach().clone().requires_grad_(True)

                msg = (
                    f"mode: '{mode}', sparse: {sparse}, padding_idx: {padding_idx}, "
                    f"allpad: {allpad}, indices.size(): {indices.size()}"
                )

                # Check forward with a Python implementation of padding_idx embedding_bag
                bag_check = embedding_bag_check(
                    indices, weights_check, mode, sparse, padding_idx
                )
                bag = torch.nn.functional.embedding_bag(
                    indices, weights, padding_idx=padding_idx, mode=mode, sparse=sparse
                )

                self.assertEqual(bag, bag_check, msg=msg)

                bag_check.sum().backward()
                grad_check = weights_check.grad

                bag.sum().backward()
                grad = weights.grad

                # Sometimes, half dtype gradients mismatch by a greater amount
                # than other dtypes
                if dtype in [torch.half, torch.bfloat16]:
                    atol = 0.01
                    rtol = 0.01
                else:
                    atol = None
                    rtol = None
                self.assertEqual(grad, grad_check, msg=msg, atol=atol, rtol=rtol)