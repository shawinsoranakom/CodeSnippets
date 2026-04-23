def _make_tensor(shape, dtype, device, fill_ones=False) -> torch.Tensor:
    # Returns a tensor filled with ones
    if fill_ones:
        return torch.ones(*shape, dtype=_convert_t(dtype, device), device=device)

    # Returns a tensor with random integer values
    if not (dtype.is_floating_point or dtype.is_complex):
        t = torch.randint(0, 10, shape, device=device)
        if dtype != torch.uint8:
            t = t - 5  # generate negative values also
        return t.to(_convert_t(dtype, device))

    # Populates the CPU tensor with floats representable as half/bfloat16
    if dtype == torch.half and device == "cpu":
        return torch.randn(*shape, dtype=torch.float, device=device).half().float()
    if dtype == torch.bfloat16 and device == "cpu":
        return torch.randn(*shape, dtype=torch.float, device=device).bfloat16().float()

    # Default: returns a tensor with random float values
    return torch.randn(shape, dtype=dtype, device=device).to(dtype=dtype)