def _untie_named_tensors_map(
    module: "torch.nn.Module",
    parameters_and_buffers: dict[str, Tensor],
) -> dict[str, Tensor]:
    """
    Unties all tied tensors in the module to parameters_and_buffers.

    This function returns a new untied_parameters_and_buffers dictionary and leave the original
    untied_parameters_and_buffers dictionary unchanged. It adds new (missing) keys for tied tensors
    in the module to untied_parameters_and_buffers. The value of the new key is the user-given value
    in the original parameters_and_buffers dictionary.

    If there are more than one user-given values for the same tied tensor, it will raise an error.

    For example, if the module has two tied weights self.foo and self.tied_foo and the user passes
    {'foo': foo_value, ...}, this will return {'foo': foo_value, 'tied_foo': foo_value, ...}. If the
    user passes {'foo': foo_value, 'tied_foo': tied_foo_value, ...}, it will raise an error. If the
    user passes {'foo': foo_value, 'tied_foo': foo_value, ...}, it will not raise an error.

    Args:
        module (torch.nn.Module): the module to determine which tensors are tied.
        parameters_and_buffers (Dict[str, Tensor]): a map of {name: tensor} for reparamaterizing the module.

    Returns:
        A new untied version of the parameters_and_buffers dictionary.

    Raises:
        ValueError: if there are more than one user-given values for the same tied tensor.
    """
    # A map of {name: tensor} for all tensors (including tied ones) in the module.
    all_named_tensors: dict[str, Tensor] = {}
    all_named_tensors.update(module.named_parameters(remove_duplicate=False))
    all_named_tensors.update(module.named_buffers(remove_duplicate=False))

    # A map of {tensor: set(all_tied_names)} for all tensor names in the module.
    tensor_to_tied_names_map: dict[Tensor, set[str]] = {}
    for name, tensor in all_named_tensors.items():
        if tensor not in tensor_to_tied_names_map:
            tensor_to_tied_names_map[tensor] = set()
        tensor_to_tied_names_map[tensor].add(name)

    # A map of {tied_name: set(all_tied_names)} for all tensor names in the module.
    # If a name is not tied, it will not be in this map.
    tied_names_map: dict[str, set[str]] = {}
    for tied_names in tensor_to_tied_names_map.values():
        if len(tied_names) > 1:
            for tied_name in tied_names:
                tied_names_map[tied_name] = tied_names

    # Make sure the user didn't pass multiple values for the same tied tensor.
    given_names = set(parameters_and_buffers.keys())
    # same as given_names.intersection(tied_names_map.keys()) but dynamo can't
    # handle that
    given_names_for_tied_tensors: set[str] = set()
    for name in given_names:
        if name in tied_names_map:
            given_names_for_tied_tensors.add(name)

    for given_name in given_names_for_tied_tensors:
        tied_names = tied_names_map[given_name]
        if (
            # Detect if there are multiple keys present for the same tied tensor.
            len(tied_names.intersection(given_names_for_tied_tensors)) > 1
            # Only raise an error if the user passed multiple values for the same tied tensor.
            # If all given values are the same, don't raise.
            and len({parameters_and_buffers[tied_name] for tied_name in tied_names})
            != 1
        ):
            raise ValueError(
                f"functional_call got multiple values for keys {sorted(tied_names)}, "
                f"which are tied. Consider using tie_weights=False"
            )

    # Untie the given named tensor map
    # Make a copy for not modifying the original dict
    untied_parameters_and_buffers = parameters_and_buffers.copy()
    for given_name in given_names_for_tied_tensors:
        for tied_name in tied_names_map[given_name]:
            untied_parameters_and_buffers[tied_name] = parameters_and_buffers[
                given_name
            ]
    return untied_parameters_and_buffers