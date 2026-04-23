def reshape_transform(transform, shape):
    # Needed to squash batch dims for testing jacobian
    if isinstance(transform, AffineTransform):
        if isinstance(transform.loc, Number):
            return transform
        try:
            return AffineTransform(
                transform.loc.expand(shape),
                transform.scale.expand(shape),
                cache_size=transform._cache_size,
            )
        except RuntimeError:
            return AffineTransform(
                transform.loc.reshape(shape),
                transform.scale.reshape(shape),
                cache_size=transform._cache_size,
            )
    if isinstance(transform, ComposeTransform):
        reshaped_parts = []
        for p in transform.parts:
            reshaped_parts.append(reshape_transform(p, shape))
        return ComposeTransform(reshaped_parts, cache_size=transform._cache_size)
    if isinstance(transform.inv, AffineTransform):
        return reshape_transform(transform.inv, shape).inv
    if isinstance(transform.inv, ComposeTransform):
        return reshape_transform(transform.inv, shape).inv
    return transform