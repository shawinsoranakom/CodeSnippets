def _copy_pooler_output_to_cpu(
    raw_pooler_output: PoolerOutput, finished_mask: list[bool]
) -> list[torch.Tensor | None]:
    num_reqs = len(finished_mask)

    if isinstance(raw_pooler_output, torch.Tensor):
        if raw_pooler_output.shape[0] != num_reqs:
            raise ValueError(
                "Pooler output batch size does not match finished mask size: "
                f"{raw_pooler_output.shape[0]} != {num_reqs}."
            )

        num_finished = sum(finished_mask)
        if num_finished == 0:
            return [None] * num_reqs
        if num_finished == num_reqs:
            return list(raw_pooler_output.to("cpu", non_blocking=True))

        # partial finished
        finished_indices = [i for i, include in enumerate(finished_mask) if include]
        index_tensor = torch.tensor(
            finished_indices, device=raw_pooler_output.device, dtype=torch.long
        )
        finished_outputs = raw_pooler_output.index_select(0, index_tensor).to(
            "cpu", non_blocking=True
        )
        partial_pooler_output: list[torch.Tensor | None] = [None] * num_reqs
        for i, out in zip(finished_indices, finished_outputs):
            partial_pooler_output[i] = out
        return partial_pooler_output

    assert isinstance(raw_pooler_output, list)
    if len(raw_pooler_output) != num_reqs:
        raise ValueError(
            "Pooler output batch size does not match finished mask size: "
            f"{len(raw_pooler_output)} != {num_reqs}."
        )

    pooler_output: list[torch.Tensor | None] = [None] * num_reqs
    for i, (out, include) in enumerate(zip(raw_pooler_output, finished_mask)):
        if include and out is not None:
            pooler_output[i] = out.to("cpu", non_blocking=True)
    return pooler_output