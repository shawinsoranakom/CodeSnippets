def test_biject_to(constraint_fn, args, is_cuda):
    constraint = build_constraint(constraint_fn, args, is_cuda=is_cuda)
    try:
        t = biject_to(constraint)
    except NotImplementedError:
        pytest.skip("`biject_to` not implemented.")
    if not t.bijective:
        raise AssertionError(f"biject_to({constraint}) is not bijective")
    if constraint_fn is constraints.corr_cholesky:
        # (D * (D-1)) / 2 (where D = 4) = 6 (size of last dim)
        x = torch.randn(6, 6, dtype=torch.double)
    else:
        x = torch.randn(5, 5, dtype=torch.double)
    if is_cuda:
        x = x.cuda()
    y = t(x)
    if not constraint.check(y).all():
        raise AssertionError(
            "\n".join(
                [
                    f"Failed to biject_to({constraint})",
                    f"x = {x}",
                    f"biject_to(...)(x) = {y}",
                ]
            )
        )
    x2 = t.inv(y)
    if not torch.allclose(x, x2):
        raise AssertionError(f"Error in biject_to({constraint}) inverse")

    j = t.log_abs_det_jacobian(x, y)
    if j.shape != x.shape[: x.dim() - t.domain.event_dim]:
        raise AssertionError(
            f"Expected shape {x.shape[: x.dim() - t.domain.event_dim]}, got {j.shape}"
        )