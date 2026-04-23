def extract_weight_comparison(m: GraphModule) -> NSResultsType:
    # example graph:
    #
    #   w1 = self.w1
    #   b1 = self.b1
    #   linear = torch._C._nn.linear(x, w1, b1)
    #   shadow_0_0 = self.shadow_0_0(linear)
    #   shadow_wrapper_0_1 = self.shadow_wrapper_0_1(x, w1, b1)
    #   shadow_0_1 = self.shadow_0_1(shadow_wrapper_0_1, linear)
    #
    # algorithm:
    # 1. for each call_function node matching our allowlist:
    # 2.   if corresponding shadow wrapper exists, extract the weight pair
    #
    # Note: this is not super robust, but that's ok because this is
    # just for legacy customers who depend on the previous two-model version
    # of this API. TBD if we need to make this robust.
    # Note: modules are not supported, since existing customers only
    # use functions.

    # TODO(future PR): move this to config
    weighted_ops = {
        torch.nn.functional.linear,
    }

    results: NSResultsType = {"model": {NSSingleResultValuesType.WEIGHT.value: {}}}

    for n in m.graph.nodes:  # type: ignore[union-attr]
        if not (n.op == "call_function" and n.target in weighted_ops):
            continue

        # Check if we have a corresponding shadow wrapper
        # TODO(future PR, if needed): support kwargs
        # TODO(future PR, if needed): support multiple shadow users
        first_arg = n.args[0]
        shadow_wrapper_node = None
        for user in first_arg.users:
            # TODO(before land): fix string match
            if user.op == "call_module" and user.target.startswith("shadow_wrapper"):
                shadow_wrapper_node = user
                break

        if shadow_wrapper_node is None:
            continue

        shadow_wrapper = getattr_from_fqn(m, shadow_wrapper_node.target)  # type: ignore[arg-type]
        weight_info = _get_weight_info_from_shadow_wrapper(shadow_wrapper)
        if weight_info is None:
            continue

        # get weight
        w_node = n.args[1]
        w_obj = getattr_from_fqn(m, w_node.target).detach()

        # get a quantized version of weight
        quant_fn, quant_fn_args_except_first = weight_info
        new_args = (w_obj, *quant_fn_args_except_first)
        w_obj_q = quant_fn(*new_args)

        # add a comparison
        ref_node_name = n.name
        prev_node_name = n.name
        ref_node_type = get_target_type_str(n, m)
        prev_node_type = ref_node_type
        fqn = None
        if hasattr(m, "_node_name_to_scope"):
            fqn = m._node_name_to_scope[n.name][0]  # type: ignore[index]
        comparison = torch.ao.ns.fx.utils.compute_sqnr(w_obj, w_obj_q)
        result_fp32 = {
            "res_type": NSSingleResultValuesType.WEIGHT.value,
            "values": [w_obj],
            "prev_node_name": prev_node_name,
            "prev_node_target_type": prev_node_type,
            "ref_node_name": ref_node_name,
            "ref_node_target_type": ref_node_type,
            "index_within_arg": 0,
            "index_of_arg": 0,
            "fqn": fqn,
            "qconfig_str": "",
            "comparisons": [comparison],
            "comparison_fn_name": "sqnr",
        }
        result_q = {
            "res_type": NSSingleResultValuesType.WEIGHT.value,
            "values": [w_obj_q],
            "prev_node_name": prev_node_name,
            "prev_node_target_type": prev_node_type,
            "ref_node_name": ref_node_name,
            "ref_node_target_type": ref_node_type,
            "index_within_arg": 0,
            "index_of_arg": 0,
            "fqn": fqn,
            "qconfig_str": "",
            "comparisons": [comparison],
            "comparison_fn_name": "sqnr",
        }

        # go from subgraph_n_1 to subgraph_n_0
        _1, _2, node_idx, _3 = shadow_wrapper_node.target.split("_")
        name_fp32 = f"subgraph_{node_idx}_0"
        name_q = f"subgraph_{node_idx}_1"

        results["model"][NSSingleResultValuesType.WEIGHT.value][name_fp32] = [
            result_fp32
        ]
        results["model"][NSSingleResultValuesType.WEIGHT.value][name_q] = [result_q]

    return results