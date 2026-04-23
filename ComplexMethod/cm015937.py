def test_embedding_bag_1D_padding_idx(self, device, dtype):
        num_features = 3
        max_indices_per_bag = 10
        num_bags = 10
        num_words = 100

        def gen_1D_indices_offsets(include_last_offset, allpad):
            indices = []
            offsets = []
            cur_offset = 0

            # Make one bag full and one bag empty, for extra coverage
            empty_bag = random.randint(0, num_bags - 1)
            full_bag = empty_bag
            while full_bag == empty_bag:
                full_bag = random.randint(0, num_bags - 1)

            for bag in range(num_bags):
                offsets.append(cur_offset)
                if bag == full_bag:
                    bag_size = max_indices_per_bag
                elif bag == empty_bag:
                    bag_size = 0
                else:
                    bag_size = random.randint(1, max_indices_per_bag - 1)
                indices += [
                    1 if allpad else random.randint(0, num_words - 1)
                    for _ in range(bag_size)
                ]
                cur_offset += bag_size

            # embedding_bag requires first entry of offsets to be 0
            if offsets[0] != 0:
                raise AssertionError(f"Expected offsets[0] == 0, got {offsets[0]}")

            indices = torch.tensor(indices, device=device)

            if include_last_offset:
                offsets.append(indices.size(0))

            offsets = torch.tensor(offsets, device=device)

            return indices, offsets

        # Convert a 1-D indices-offsets representation into 2-D. Fill any empty
        # indices with padding_idx
        def gen_2D_indices_from_1D(
            indices_1D, offsets, include_last_offset, padding_idx
        ):
            if offsets[0] != 0:
                raise AssertionError(f"Expected offsets[0] == 0, got {offsets[0]}")
            if include_last_offset:
                offsets = offsets[:-1]
            indices_2D = torch.empty(
                num_bags, max_indices_per_bag, device=device, dtype=torch.long
            )
            for bag in range(num_bags):
                # Determine the start and end position of the bag within indices_1D
                start = offsets[bag]
                end = len(indices_1D) if bag + 1 == num_bags else offsets[bag + 1]
                end = min(len(indices_1D), end)

                # Pull out the bag's indices from indices_1D, and fill any
                # remaining space with padding indices
                indices_in_bag = []
                for item_pos in range(max_indices_per_bag):
                    if (start + item_pos) < end:
                        indices_in_bag.append(indices_1D[start + item_pos])
                    else:
                        indices_in_bag.append(padding_idx)
                indices_2D[bag] = torch.tensor(indices_in_bag, device=device)

            return indices_2D

        test_cases = product(
            ["max", "mean", "sum"], [False, True], [False, True], [False, True]
        )

        for mode, sparse, include_last_offset, allpad in test_cases:
            # Max sparse and bfloat16 are not supported
            if mode == "max":
                if sparse or (dtype == torch.bfloat16):
                    continue
            indices_1D, offsets = gen_1D_indices_offsets(include_last_offset, allpad)
            for padding_idx_1D in list(set(indices_1D.tolist())) + [None]:
                msg = (
                    f"mode: '{mode}', sparse: {sparse}, include_last_offset: {include_last_offset}, "
                    f"padding_idx_1D: {padding_idx_1D}"
                )

                # If 1D input does not use a padding index, we still need one for the 2D input,
                # so we can add one dummy word to the weights to act as the padded word
                padding_idx_2D = (
                    padding_idx_1D if padding_idx_1D is not None else num_words
                )
                num_words_with_padding = (
                    num_words if padding_idx_1D is not None else num_words + 1
                )

                indices_2D = gen_2D_indices_from_1D(
                    indices_1D, offsets, include_last_offset, padding_idx_2D
                )

                weights = torch.randn(
                    num_words_with_padding,
                    num_features,
                    dtype=dtype,
                    device=device,
                    requires_grad=True,
                )
                weights_check = weights.detach().clone().requires_grad_(True)

                bag = torch.nn.functional.embedding_bag(
                    indices_1D,
                    weights,
                    offsets,
                    padding_idx=padding_idx_1D,
                    mode=mode,
                    sparse=sparse,
                    include_last_offset=include_last_offset,
                )

                bag_check = torch.nn.functional.embedding_bag(
                    indices_2D,
                    weights_check,
                    padding_idx=padding_idx_2D,
                    mode=mode,
                    sparse=sparse,
                )
                self.assertEqual(bag, bag_check, msg=msg)

                bag.sum().backward()
                bag_check.sum().backward()

                # Sometimes, half dtype gradients mismatch by a greater amount
                # than other dtypes
                if dtype in [torch.half, torch.bfloat16]:
                    atol = 0.01
                    rtol = 0.01
                else:
                    atol = None
                    rtol = None
                self.assertEqual(
                    weights.grad, weights_check.grad, msg=msg, atol=atol, rtol=rtol
                )