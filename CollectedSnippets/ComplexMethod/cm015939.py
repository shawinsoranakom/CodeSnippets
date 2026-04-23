def _embedding_bag_reference_impl(
        self,
        input,
        weight,
        offsets=None,
        mode="sum",
        per_sample_weights=None,
        include_last_offset=False,
    ):
        if mode != "sum" and per_sample_weights is not None:
            raise AssertionError(
                f"per_sample_weights must be None for mode '{mode}', got {per_sample_weights}"
            )
        if offsets is None:
            raise AssertionError("offsets must not be None")
        if per_sample_weights is None:
            per_sample_weights = torch.ones(input.size()).to(
                dtype=weight.dtype, device=weight.device
            )
        if input.numel() != per_sample_weights.numel():
            raise AssertionError(
                f"Expected input.numel() == per_sample_weights.numel(), got {input.numel()} vs {per_sample_weights.numel()}"
            )

        bags = []
        long_input = input.to(torch.long)
        embeddings = weight.index_select(0, long_input) * per_sample_weights.unsqueeze(
            1
        )
        if include_last_offset:
            for index in range(len(offsets) - 1):
                offset = offsets[index]
                next_offset = offsets[index + 1]
                length = next_offset - offset
                if length == 0:
                    bags.append(
                        torch.tensor([0] * weight.size(1)).to(
                            dtype=embeddings.dtype, device=embeddings.device
                        )
                    )
                else:
                    if mode == "sum":
                        bags.append(embeddings.narrow(0, offset, length).sum(0))
                    elif mode == "mean":
                        bags.append(
                            embeddings.narrow(0, offset, length).sum(0).div(length)
                        )
                    else:
                        if mode != "max":
                            raise AssertionError(
                                f"Expected mode == 'max', got '{mode}'"
                            )
                        bags.append(embeddings.narrow(0, offset, length).max(0)[0])
        else:
            for index, offset in enumerate(offsets):
                if index + 1 < len(offsets):
                    next_offset = offsets[index + 1]
                else:
                    next_offset = len(long_input)
                length = next_offset - offset
                if length == 0:
                    bags.append(
                        torch.tensor([0] * weight.size(1)).to(
                            dtype=embeddings.dtype, device=embeddings.device
                        )
                    )
                else:
                    if mode == "sum":
                        bags.append(embeddings.narrow(0, offset, length).sum(0))
                    elif mode == "mean":
                        bags.append(
                            embeddings.narrow(0, offset, length).sum(0).div(length)
                        )
                    else:
                        if mode != "max":
                            raise AssertionError(
                                f"Expected mode == 'max', got '{mode}'"
                            )
                        bags.append(embeddings.narrow(0, offset, length).max(0)[0])
        return torch.stack(bags)