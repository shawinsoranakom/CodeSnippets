def test_compose_affine(event_dims):
    transforms = [
        AffineTransform(torch.zeros((1,) * e), 1, event_dim=e) for e in event_dims
    ]
    transform = ComposeTransform(transforms)
    if transform.codomain.event_dim != max(event_dims):
        raise AssertionError(
            f"Expected codomain.event_dim {max(event_dims)}, got {transform.codomain.event_dim}"
        )
    if transform.domain.event_dim != max(event_dims):
        raise AssertionError(
            f"Expected domain.event_dim {max(event_dims)}, got {transform.domain.event_dim}"
        )

    base_dist = Normal(0, 1)
    if transform.domain.event_dim:
        base_dist = base_dist.expand((1,) * transform.domain.event_dim)
    dist = TransformedDistribution(base_dist, transform.parts)
    if dist.support.event_dim != max(event_dims):
        raise AssertionError(
            f"Expected support.event_dim {max(event_dims)}, got {dist.support.event_dim}"
        )

    base_dist = Dirichlet(torch.ones(5))
    if transform.domain.event_dim > 1:
        base_dist = base_dist.expand((1,) * (transform.domain.event_dim - 1))
    dist = TransformedDistribution(base_dist, transforms)
    if dist.support.event_dim != max(1, *event_dims):
        raise AssertionError(
            f"Expected support.event_dim {max(1, *event_dims)}, got {dist.support.event_dim}"
        )