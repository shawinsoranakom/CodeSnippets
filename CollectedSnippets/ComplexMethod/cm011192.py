def _combine_any_rank_results(rank_results: dict[int, Any]) -> Any:
    any_v = next(iter(rank_results.values()))

    if isinstance(any_v, Tensor):
        # pyrefly: ignore [bad-argument-type, bad-argument-count]
        return LocalTensor(rank_results)

    if isinstance(any_v, int):
        return _combine_int_rank_results(rank_results)

    if isinstance(any_v, torch.device):
        if not all(v.type == any_v.type for v in rank_results.values()):
            raise AssertionError("device type should be the same")
        # Just use the first device - the device type is what matters,
        # and LocalTensorMode runs on a single physical device anyway
        return any_v

    if not all(v == any_v for v in rank_results.values()):
        raise AssertionError(
            "Non Tensor or int rank results must be equal for all ranks"
        )

    return any_v