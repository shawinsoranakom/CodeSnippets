def get_routing_method_type(
    scoring_func: str,
    top_k: int,
    renormalize: bool,
    num_expert_group: int | None,
    has_e_score_bias: bool,
) -> RoutingMethodType:
    if has_e_score_bias:
        if (num_expert_group or 0) > 0 and scoring_func == "sigmoid":
            return RoutingMethodType.DeepSeekV3
        else:
            return RoutingMethodType.Unspecified

    if scoring_func == "sigmoid":
        if top_k == 1:
            return RoutingMethodType.Llama4
        else:
            return RoutingMethodType.Unspecified

    if scoring_func == "softmax":
        if renormalize:
            return RoutingMethodType.Renormalize
        else:
            return RoutingMethodType.Default

    return RoutingMethodType.Unspecified