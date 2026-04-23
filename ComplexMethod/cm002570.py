def remove_tied_weights_from_state_dict(
    state_dict: dict[str, torch.Tensor], model: "PreTrainedModel"
) -> dict[str, torch.Tensor]:
    """
    Remove all tied weights from the given `state_dict`, making sure to keep only the main weight that `model`
    will expect when reloading (even if we now tie weights symmetrically, it's better to keep the intended one).
    This is because `safetensors` does not allow tensor aliasing - so we're going to remove aliases before saving.
    """
    # To avoid any potential mistakes and mismatches between config and actual tied weights, here we check the pointers
    # of the Tensors themselves -> we are guaranteed to find all the actual tied weights
    ptrs = collections.defaultdict(list)
    for name, tensor in state_dict.items():
        if not isinstance(tensor, torch.Tensor):
            # Sometimes in the state_dict we have non-tensor objects.
            # e.g. in bitsandbytes we have some `str` objects in the state_dict
            # In the non-tensor case, fall back to the pointer of the object itself
            ptrs[id(tensor)].append(name)

        elif tensor.device.type == "meta":
            # In offloaded cases, there may be meta tensors in the state_dict.
            # For these cases, key by the pointer of the original tensor object
            # (state_dict tensors are detached and therefore no longer shared)
            tensor = model.get_parameter(name)
            ptrs[id(tensor)].append(name)

        else:
            ptrs[id_tensor_storage(tensor)].append(name)

    shared_ptrs = {ptr: names for ptr, names in ptrs.items() if len(names) > 1}

    # Recursively descend to find tied weight keys
    all_potential_tied_weights_keys = set(_get_tied_weight_keys(model))
    error_names = []
    to_delete_names = set()
    # Removing the keys which are declared as known duplicates on load. This allows to make sure the name which is
    # kept is consistent
    if all_potential_tied_weights_keys is not None:
        for names in shared_ptrs.values():
            found = 0
            for name in sorted(names):
                matches_pattern = any(re.search(pat, name) for pat in all_potential_tied_weights_keys)
                if matches_pattern and name in state_dict:
                    found += 1
                    if found < len(names):
                        to_delete_names.add(name)
    # We are entering a place where the weights and the transformers configuration do NOT match.
    shared_names, disjoint_names = _find_disjoint(shared_ptrs.values(), state_dict)
    # Those are actually tensor sharing but disjoint from each other, we can safely clone them
    # Reloaded won't have the same property, but it shouldn't matter in any meaningful way.
    for name in disjoint_names:
        state_dict[name] = state_dict[name].clone()

    # When not all duplicates have been cleaned, still remove those keys, but put a clear warning.
    # If the link between tensors was done at runtime then `from_pretrained` will not get
    # the key back leading to random tensor. A proper warning will be shown
    # during reload (if applicable), but since the file is not necessarily compatible with
    # the config, better show a proper warning.
    shared_names, identical_names = _find_identical(shared_names, state_dict)
    # delete tensors that have identical storage
    for inames in identical_names:
        known = inames.intersection(to_delete_names)
        for name in known:
            del state_dict[name]
        unknown = inames.difference(to_delete_names)
        if len(unknown) > 1:
            error_names.append(unknown)

    if shared_names:
        error_names.extend(shared_names)

    if len(error_names) > 0:
        raise RuntimeError(
            f"The weights trying to be saved contained shared tensors {error_names} which are not properly defined. "
            f"We found all the potential target tied weights keys to be: {all_potential_tied_weights_keys}.\n"
            "This can also just mean that the module's tied weight keys are wrong vs the actual tied weights in the model.",
        )

    return state_dict