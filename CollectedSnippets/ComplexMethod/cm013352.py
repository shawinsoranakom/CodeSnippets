def sample_inputs_linalg_ldl_solve(
    op_info, device, dtype, requires_grad=False, **kwargs
):
    # Generate LDL factors of symmetric (and Hermitian on CPU) matrices
    from torch.testing._internal.common_utils import (
        random_hermitian_pd_matrix,
        random_symmetric_pd_matrix,
    )

    device = torch.device(device)
    symmetric_inputs = (
        random_symmetric_pd_matrix(S, dtype=dtype, device=device),  # single matrix
        random_symmetric_pd_matrix(
            S, 2, dtype=dtype, device=device
        ),  # batch of matrices
        torch.zeros(0, 0, dtype=dtype, device=device),  # 0x0 matrix
        torch.zeros(0, 2, 2, dtype=dtype, device=device),  # zero batch of matrices
    )
    hermitian_inputs = (
        (
            random_hermitian_pd_matrix(S, dtype=dtype, device=device),
            random_hermitian_pd_matrix(S, 2, dtype=dtype, device=device),
        )
        if device.type == "cpu" and dtype.is_complex
        else ()
    )
    test_cases1 = (
        torch.linalg.ldl_factor_ex(a, hermitian=False) for a in symmetric_inputs
    )
    test_cases2 = (
        torch.linalg.ldl_factor_ex(a, hermitian=True) for a in hermitian_inputs
    )

    # Symmetric case
    make_arg = partial(
        make_tensor, device=device, dtype=dtype, requires_grad=requires_grad
    )
    for test_case in test_cases1:
        factors, pivots, _ = test_case
        factors.requires_grad = requires_grad
        for B_batch_shape in ((), factors.shape[:-2]):
            B = make_arg((*B_batch_shape, factors.shape[-1], S))
            yield SampleInput(factors, args=(pivots, B), kwargs=dict(hermitian=False))
            clone_factors = factors.detach().clone().requires_grad_(requires_grad)
            yield SampleInput(
                clone_factors, args=(pivots, B), kwargs=dict(hermitian=False)
            )

    # Hermitian case
    for test_case in test_cases2:
        factors, pivots, _ = test_case
        factors.requires_grad = requires_grad
        for B_batch_shape in ((), factors.shape[:-2]):
            B = make_arg((*B_batch_shape, factors.shape[-1], S))
            yield SampleInput(factors, args=(pivots, B), kwargs=dict(hermitian=True))
            clone_factors = factors.detach().clone().requires_grad_(requires_grad)
            yield SampleInput(
                clone_factors, args=(pivots, B), kwargs=dict(hermitian=True)
            )