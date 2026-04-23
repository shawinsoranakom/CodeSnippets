def __init__(
        self,
        base_distribution: Distribution,
        transforms: Transform | list[Transform],
        validate_args: bool | None = None,
    ) -> None:
        if isinstance(transforms, Transform):
            self.transforms = [
                transforms,
            ]
        elif isinstance(transforms, list):
            if not all(isinstance(t, Transform) for t in transforms):
                raise ValueError(
                    "transforms must be a Transform or a list of Transforms"
                )
            self.transforms = transforms
        else:
            raise ValueError(
                f"transforms must be a Transform or list, but was {transforms}"
            )

        # Reshape base_distribution according to transforms.
        base_shape = base_distribution.batch_shape + base_distribution.event_shape
        base_event_dim = len(base_distribution.event_shape)
        transform = ComposeTransform(self.transforms)
        if len(base_shape) < transform.domain.event_dim:
            raise ValueError(
                f"base_distribution needs to have shape with size at least {transform.domain.event_dim}, but got {base_shape}."
            )
        forward_shape = transform.forward_shape(base_shape)
        expanded_base_shape = transform.inverse_shape(forward_shape)
        if base_shape != expanded_base_shape:
            base_batch_shape = expanded_base_shape[
                : len(expanded_base_shape) - base_event_dim
            ]
            base_distribution = base_distribution.expand(base_batch_shape)
        reinterpreted_batch_ndims = transform.domain.event_dim - base_event_dim
        if reinterpreted_batch_ndims > 0:
            base_distribution = Independent(
                base_distribution, reinterpreted_batch_ndims
            )
        self.base_dist = base_distribution

        # Compute shapes.
        transform_change_in_event_dim = (
            transform.codomain.event_dim - transform.domain.event_dim
        )
        event_dim = max(
            transform.codomain.event_dim,  # the transform is coupled
            base_event_dim + transform_change_in_event_dim,  # the base dist is coupled
        )
        if len(forward_shape) < event_dim:
            raise AssertionError(
                f"forward_shape length {len(forward_shape)} must be >= event_dim {event_dim}"
            )
        cut = len(forward_shape) - event_dim
        batch_shape = forward_shape[:cut]
        event_shape = forward_shape[cut:]
        super().__init__(batch_shape, event_shape, validate_args=validate_args)