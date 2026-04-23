def test_forward_inverse(transform, test_cached):
    x = generate_data(transform).requires_grad_()
    if not transform.domain.check(x).all():
        raise AssertionError("Input data are not valid for domain")
    try:
        y = transform(x)
    except NotImplementedError:
        pytest.skip("Not implemented.")
    if y.shape != transform.forward_shape(x.shape):
        raise AssertionError(
            f"Expected y.shape {transform.forward_shape(x.shape)}, got {y.shape}"
        )
    if test_cached:
        x2 = transform.inv(y)  # should be implemented at least by caching
    else:
        try:
            x2 = transform.inv(y.clone())  # bypass cache
        except NotImplementedError:
            pytest.skip("Not implemented.")
    if x2.shape != transform.inverse_shape(y.shape):
        raise AssertionError(
            f"Expected x2.shape {transform.inverse_shape(y.shape)}, got {x2.shape}"
        )
    y2 = transform(x2)
    if transform.bijective:
        # verify function inverse
        if not torch.allclose(x2, x, atol=1e-4, equal_nan=True):
            raise AssertionError(
                "\n".join(
                    [
                        f"{transform} t.inv(t(-)) error",
                        f"x = {x}",
                        f"y = t(x) = {y}",
                        f"x2 = t.inv(y) = {x2}",
                    ]
                )
            )
    else:
        # verify weaker function pseudo-inverse
        if not torch.allclose(y2, y, atol=1e-4, equal_nan=True):
            raise AssertionError(
                "\n".join(
                    [
                        f"{transform} t(t.inv(t(-))) error",
                        f"x = {x}",
                        f"y = t(x) = {y}",
                        f"x2 = t.inv(y) = {x2}",
                        f"y2 = t(x2) = {y2}",
                    ]
                )
            )