def verify_tp_plan(expected_keys: list[str], tp_plan: dict[str, str] | None):
    """
    Verify the TP plan of the model, log a warning if the layers that were not sharded and the rules that were not applied.
    """

    if tp_plan is None:
        return

    generic_keys = {replace_layer_number_by_wildcard(key) for key in expected_keys}
    unsharded_layers = set(generic_keys)
    unused_rules = tp_plan.copy()

    for key in generic_keys:
        param_name = key.rsplit(".", 1)[0] if "." in key else key
        generic_param_name = re.sub(r"\d+", "*", param_name)

        if generic_param_name in tp_plan:
            unused_rules.pop(generic_param_name, None)
            unsharded_layers.discard(key)
        elif "." in generic_param_name and (parent_param_name := generic_param_name.rsplit(".", 1)[0]) in tp_plan:
            unused_rules.pop(parent_param_name, None)
            unsharded_layers.discard(key)

    if len(unused_rules) > 0:
        logger.warning(f"The following TP rules were not applied on any of the layers: {unused_rules}")
    if len(unsharded_layers) > 0:
        logger.warning(f"The following layers were not sharded: {', '.join(unsharded_layers)}")