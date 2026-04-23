def check_mamba_state_equal(
    mamba_state_ref: dict, mamba_state_new: dict, keys_to_check: list[int]
):
    atol = 1e-2
    rtol = 1e-2
    for key in keys_to_check:
        assert key in mamba_state_new
        assert key in mamba_state_ref
        # mamba state new is a subset of mamba state ref
        for i, (ref, new) in enumerate(zip(mamba_state_ref[key], mamba_state_new[key])):
            if ref.device != new.device:
                new = new.to(ref.device)
            new = new[: ref.shape[0]]
            if not torch.allclose(ref, new, atol=atol, rtol=rtol):
                diff_mask = ~torch.isclose(ref, new, atol=atol, rtol=rtol)
                diff_idx = torch.nonzero(diff_mask)
                if diff_idx.shape[0] * 100 < ref.numel():
                    print(
                        f"[WARNING] found {diff_idx.shape[0] * 100 / ref.numel()}% of the elements are different"  # noqa: E501
                    )
                    continue
                raise ValueError(
                    f"Mamba state is not equal for key: {key} at index {i}"
                )
    return True