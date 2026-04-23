def dropout(inputs, rate, noise_shape=None, seed=None):
    if rate == 1.0:
        return torch.zeros_like(inputs, device=get_device())
    if rate == 0.0:
        return inputs
    if (
        seed is not None
        and not (isinstance(seed, SeedGenerator) and seed._initial_seed is None)
        or noise_shape is not None
    ):
        keep_prob = 1.0 - rate
        noise_shape = _get_concrete_noise_shape(inputs, noise_shape)
        keep_prob_matrix = torch.full(
            noise_shape, keep_prob, device=get_device()
        )
        generator = torch_seed_generator(seed)

        # Do not use generator during symbolic execution.
        if get_device() == "meta":
            mask = torch.bernoulli(keep_prob_matrix)
        else:
            mask = torch.bernoulli(keep_prob_matrix, generator=generator)

        mask = mask.bool()
        mask = torch.broadcast_to(mask, inputs.shape)
        return torch.where(
            mask,
            inputs / keep_prob,
            torch.zeros_like(inputs, dtype=inputs.dtype),
        )
    # Fast path, unseeded (since torch doesn't support seeding dropout!!!!)
    # Using the above implementation is possible, but much slower.
    return torch.nn.functional.dropout(
        inputs, p=rate, training=True, inplace=False
    )