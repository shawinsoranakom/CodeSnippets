def check_expert_grads(
    ref_result: BackwardResult,
    test_result: BackwardResult,
    atol: float,
    rtol: float,
    verbose: bool = False,
):
    fields_to_check = [f.name for f in fields(BackwardResult) if "proj" in f.name]
    assert len(fields_to_check) == 3

    for field in fields_to_check:
        ref_grads = getattr(ref_result, field)
        test_grads = getattr(test_result, field)
        assert (
            ref_grads.shape == test_grads.shape
        ), f"{field}: {ref_grads.shape} != {test_grads.shape}"

        # Test each expert
        for i in range(ref_grads.shape[0]):
            ref_grad = ref_grads[i]
            test_grad = test_grads[i]
            diff = (ref_grad - test_grad).abs().max()
            assert torch.allclose(
                ref_grad, test_grad, atol = atol, rtol = rtol
            ), f"{field}[{i}] diff: {diff.detach().cpu().item():.6f}"

        # Test all experts
        diff = (ref_grads - test_grads).abs().max()
        if verbose:
            print(f"{field} diff: {diff.detach().cpu().item():.6f}")
        assert torch.allclose(
            ref_grads, test_grads, atol = atol, rtol = rtol
        ), f"{field} diff: {diff.detach().cpu().item():.6f}"