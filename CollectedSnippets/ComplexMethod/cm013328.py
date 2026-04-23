def sample_inputs_foreach(
    self,
    device,
    dtype,
    N,
    *,
    noncontiguous=False,
    same_size=False,
    low=None,
    high=None,
    # zero_size means EVERY input is empty
    zero_size: bool,
    requires_grad: bool,
    # mutually exclusive from same_size and zero_size, which are all or nothing
    intersperse_empty_tensors: bool = False,
):
    if zero_size:
        return [torch.empty(0, dtype=dtype, device=device) for _ in range(N)]
    if same_size:
        return [
            make_tensor(
                (N, N),
                dtype=dtype,
                device=device,
                noncontiguous=noncontiguous,
                low=low,
                high=high,
                requires_grad=requires_grad,
            )
            for _ in range(N)
        ]
    else:
        # interweave some empty tensors + have the last 2 tensors be empty (see #100701)
        return [
            torch.empty(0, dtype=dtype, device=device, requires_grad=requires_grad)
            if (i % 3 == 0 or i >= N - 2) and intersperse_empty_tensors
            else make_tensor(
                (N - i, N - i),
                dtype=dtype,
                device=device,
                noncontiguous=noncontiguous,
                low=low,
                high=high,
                requires_grad=requires_grad,
            )
            for i in range(N)
        ]