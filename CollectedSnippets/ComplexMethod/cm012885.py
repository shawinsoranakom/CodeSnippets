def get_op_node_and_weight_eq_obs(
    input_eq_obs_node: Node, model: GraphModule, modules: dict[str, nn.Module]
) -> tuple[Node | None, _WeightEqualizationObserver | None]:
    """Gets the following weight equalization observer. There should always
    exist a weight equalization observer after an input equalization observer.

    Returns the operation node that follows the input equalization observer node
    and the weight equalization observer
    """

    # Find the op node that comes directly after the input equalization observer
    op_node = None
    for user in input_eq_obs_node.users:
        if node_supports_equalization(user, modules):
            op_node = user
            break

    if op_node is None:
        raise AssertionError(
            "Expected an operation node after the input equalization observer"
        )
    if op_node.op == "call_module":
        # If the op_node is a nn.Linear layer, then it must have a
        # WeightEqualizationObserver configuration
        maybe_equalization_node_name_to_config = _get_observed_graph_module_attr(
            model, "equalization_node_name_to_qconfig"
        )
        if maybe_equalization_node_name_to_config is None:
            raise AssertionError(
                "Expected 'equalization_node_name_to_qconfig' attribute in observed graph module"
            )
        equalization_node_name_to_qconfig: dict[str, Any] = (
            maybe_equalization_node_name_to_config  # type: ignore[assignment]
        )
        if equalization_node_name_to_qconfig.get(op_node.name) is None:
            raise AssertionError(
                f"No equalization qconfig found for op node {op_node.name}"
            )
        weight_eq_obs = equalization_node_name_to_qconfig.get(op_node.name).weight()  # type: ignore[union-attr]

        if not isinstance(weight_eq_obs, _WeightEqualizationObserver):
            raise AssertionError(
                "Expected weight equalization observer to be a _WeightEqualizationObserver"
            )
        return op_node, weight_eq_obs

    elif op_node.op == "call_function":
        weight_node = maybe_get_weight_eq_obs_node(op_node, modules)
        if weight_node is not None:
            weight_eq_obs = modules[str(weight_node.target)]
            if not isinstance(weight_eq_obs, _WeightEqualizationObserver):
                raise AssertionError(
                    "Expected weight equalization observer to be a _WeightEqualizationObserver"
                )
            return op_node, weight_eq_obs

    return None, None