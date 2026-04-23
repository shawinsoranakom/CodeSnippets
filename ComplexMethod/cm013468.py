def track_dynamism_across_examples(
    example_inputs: list[Any],
) -> dict[Any, Any]:
    """
    This function analyzes a list of example inputs to determine the dynamism of their shapes.
    It tracks whether the dimensions of tensors or non-tensor values change across
    different examples. The function returns a dictionary where each key represents
    a path to a value in the input examples, and the corresponding value is a tuple
    indicating which dimensions are dynamic (i.e., change across examples). This
    helps in understanding how the structure of data varies across different instances.
    """
    tracking: dict[KeyPath, tuple[list[set[Any]], bool]] = {}

    for ex in example_inputs:
        if "self" in ex and isinstance(ex["self"], torch.nn.Module):
            ex["self"] = module_to_nested_dict(ex["self"])
        leaves_with_paths, _ = tree_flatten_with_path(ex)
        for key_path, value in leaves_with_paths:
            if not isinstance(value, (int, float, torch.Tensor)):
                continue
            if isinstance(value, torch.Tensor):
                shape: tuple[int | float, ...] = tuple(value.shape)
                is_tensor = True
            else:
                shape = (value,)
                is_tensor = False
            if key_path not in tracking:
                tracking[key_path] = ([set() for _ in range(len(shape))], is_tensor)
            else:
                dim_sets, flag = tracking[key_path]
                if flag != is_tensor:
                    pass
                while len(dim_sets) < len(shape):
                    dim_sets.append(set())
            for i, dim in enumerate(shape):
                tracking[key_path][0][i].add(dim)

    output: dict[Any, Any] = {}
    for key_path, (dim_sets, _is_tensor) in tracking.items():
        final_dyn = tuple(len(s) > 1 for s in dim_sets)
        key_str = "L" + "".join(f"{str(k)}" for k in key_path)
        key = key_path[0].key  # type: ignore[attr-defined]
        if key not in output:
            output[key] = {}
        output[key][key_str] = final_dyn
    return output