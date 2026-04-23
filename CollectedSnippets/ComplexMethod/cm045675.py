def coerce_arrays_pair(left: Array, right: Array) -> tuple[Array, Array]:
    if left.wrapped == ANY and right.wrapped != ANY:
        left = Array(n_dim=left.n_dim, wrapped=right.wrapped)
    if right.wrapped == ANY and left.wrapped != ANY:
        right = Array(n_dim=right.n_dim, wrapped=left.wrapped)
    if left.n_dim is None and right.n_dim is not None:
        right = Array(n_dim=None, wrapped=right.wrapped)
    if right.n_dim is None and left.n_dim is not None:
        left = Array(n_dim=None, wrapped=left.wrapped)
    return left, right