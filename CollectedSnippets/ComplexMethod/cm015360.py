def test_jacobian(transform):
    x = generate_data(transform)
    try:
        y = transform(x)
        actual = transform.log_abs_det_jacobian(x, y)
    except NotImplementedError:
        pytest.skip("Not implemented.")
    # Test shape
    target_shape = x.shape[: x.dim() - transform.domain.event_dim]
    if actual.shape != target_shape:
        raise AssertionError(f"Expected shape {target_shape}, got {actual.shape}")

    # Expand if required
    transform = reshape_transform(transform, x.shape)
    ndims = len(x.shape)
    event_dim = ndims - transform.domain.event_dim
    x_ = x.view((-1,) + x.shape[event_dim:])
    n = x_.shape[0]
    # Reshape to squash batch dims to a single batch dim
    transform = reshape_transform(transform, x_.shape)

    # 1. Transforms with unit jacobian
    if isinstance(transform, ReshapeTransform) or isinstance(
        transform.inv, ReshapeTransform
    ):
        expected = x.new_zeros(x.shape[x.dim() - transform.domain.event_dim])
        expected = x.new_zeros(x.shape[x.dim() - transform.domain.event_dim])
    # 2. Transforms with 0 off-diagonal elements
    elif transform.domain.event_dim == 0:
        jac = jacobian(transform, x_)
        # assert off-diagonal elements are zero
        if not torch.allclose(jac, jac.diagonal().diag_embed()):
            raise AssertionError("Off-diagonal elements are not zero")
        expected = jac.diagonal().abs().log().reshape(x.shape)
    # 3. Transforms with non-0 off-diagonal elements
    else:
        if isinstance(transform, CorrCholeskyTransform):
            jac = jacobian(lambda x: tril_matrix_to_vec(transform(x), diag=-1), x_)
        elif isinstance(transform.inv, CorrCholeskyTransform):
            jac = jacobian(
                lambda x: transform(vec_to_tril_matrix(x, diag=-1)),
                tril_matrix_to_vec(x_, diag=-1),
            )
        elif isinstance(transform, StickBreakingTransform):
            jac = jacobian(lambda x: transform(x)[..., :-1], x_)
        else:
            jac = jacobian(transform, x_)

        # Note that jacobian will have shape (batch_dims, y_event_dims, batch_dims, x_event_dims)
        # However, batches are independent so this can be converted into a (batch_dims, event_dims, event_dims)
        # after reshaping the event dims (see above) to give a batched square matrix whose determinant
        # can be computed.
        gather_idx_shape = list(jac.shape)
        gather_idx_shape[-2] = 1
        gather_idxs = (
            torch.arange(n)
            .reshape((n,) + (1,) * (len(jac.shape) - 1))
            .expand(gather_idx_shape)
        )
        jac = jac.gather(-2, gather_idxs).squeeze(-2)
        out_ndims = jac.shape[-2]
        jac = jac[
            ..., :out_ndims
        ]  # Remove extra zero-valued dims (for inverse stick-breaking).
        expected = torch.slogdet(jac).logabsdet

    if not torch.allclose(actual, expected, atol=1e-5):
        raise AssertionError("Jacobian computation does not match expected")