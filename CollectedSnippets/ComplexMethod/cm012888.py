def update_obs_for_equalization(
    model: GraphModule, modules: dict[str, nn.Module]
) -> dict[str, _WeightEqualizationObserver]:
    """Update all of the observer's equalization scale. For each
    InputEqualizationObserver, we will find the location of the next
    WeightEqualizationObserver, create it, and calculate the equalization scale
    based on the two observers.

    We will then return a dictionary mapping operation node names to
    the corresponding WeightEqualizationObservers for that operation.
    """
    weight_eq_obs_dict = {}
    for node in model.graph.nodes:
        if node.op == "call_module" and isinstance(
            modules[node.target], _InputEqualizationObserver
        ):
            input_eq_obs = modules[node.target]
            if not isinstance(input_eq_obs, _InputEqualizationObserver):
                raise AssertionError(
                    "Expected module at node.target to be an _InputEqualizationObserver"
                )
            op_node, weight_eq_obs = get_op_node_and_weight_eq_obs(node, model, modules)

            if op_node is None or weight_eq_obs is None:
                continue

            if op_node.op == "call_module":
                # Calibrate the weight equalization observer since it has just
                # been created
                if fused_module_supports_equalization(modules[str(op_node.target)]):
                    module = modules[str(op_node.target)][0]  # type: ignore[index]
                    if not nn_module_supports_equalization(module):
                        raise AssertionError(
                            "Expected fused module to support equalization"
                        )
                    weight_eq_obs(module.weight)
                else:
                    weight_eq_obs(modules[str(op_node.target)].weight)

            # Calculate and set the equalization scale values
            equalization_scale = calculate_equalization_scale(
                input_eq_obs, weight_eq_obs
            )
            input_eq_obs.set_equalization_scale(equalization_scale)
            weight_eq_obs.set_equalization_scale(equalization_scale)

            weight_eq_obs_dict[op_node.name] = weight_eq_obs

    return weight_eq_obs_dict