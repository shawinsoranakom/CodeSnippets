def random_nt(
    device,
    dtype,
    num_tensors,
    max_dims,
    min_dims=None,
    layout=torch.strided,
    require_non_empty=True,
):
    if min_dims is None:
        min_dims = tuple([0] * len(max_dims))

    if len(max_dims) != len(min_dims):
        raise AssertionError(
            f"Expected len(max_dims) == len(min_dims), "
            f"got {len(max_dims)} vs {len(min_dims)}"
        )
    for min_dim, max_dim in zip(min_dims, max_dims):
        if max_dim <= min_dim:
            raise AssertionError("random_nt: max_dim must be greater than min_dim")
        if min_dim < 0:
            raise AssertionError("random_nt: min_dim must be non-negative")
        if require_non_empty:
            if min_dim == 0 and max_dim == 1:
                raise AssertionError(
                    "random_nt: zero cannot be the only possible value "
                    "if require_non_empty is True"
                )

    if require_non_empty:
        # Select a random idx that will be required to be non-empty
        non_zero_idx = torch.randint(low=0, high=num_tensors, size=(1,)).item()

    ts1 = []
    for i, _ in enumerate(range(num_tensors)):
        tensor_dims = []
        for min_dim, max_dim in zip(min_dims, max_dims):
            new_min_dim = min_dim
            if require_non_empty and i == non_zero_idx and min_dim == 0:
                new_min_dim = 1
            tensor_dims.append(
                torch.randint(low=new_min_dim, high=max_dim, size=(1,)).item()
            )
        t1 = torch.randn(tensor_dims, device=device, dtype=dtype)
        ts1.append(t1)

    return torch.nested.nested_tensor(ts1, device=device, dtype=dtype, layout=layout)