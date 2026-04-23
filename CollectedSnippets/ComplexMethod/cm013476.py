def fuse(
    model: torch.nn.Module, inplace: bool = False, no_trace: bool = False
) -> torch.nn.Module:
    """
    Fuses convolution/BN and linear/BN layers for inference purposes.
    Will deepcopy your model by default, but can modify the model inplace as well.
    """
    patterns = [
        (nn.Conv1d, nn.BatchNorm1d),
        (nn.Conv2d, nn.BatchNorm2d),
        (nn.Conv3d, nn.BatchNorm3d),
        (nn.Linear, nn.BatchNorm1d),
    ]
    if not inplace:
        model = copy.deepcopy(model)
    if not no_trace or not isinstance(model, torch.fx.GraphModule):
        fx_model = fx.symbolic_trace(model)
    else:
        fx_model = model
    modules = dict(fx_model.named_modules())
    new_graph = copy.deepcopy(fx_model.graph)

    for pattern in patterns:
        for node in new_graph.nodes:
            if matches_module_pattern(pattern, node, modules):
                if len(node.args[0].users) > 1:
                    # Output of conv/linear is used by other nodes
                    continue
                first_layer = modules[node.args[0].target]
                bn = modules[node.target]
                if not bn.track_running_stats:
                    continue
                if pattern[0] in [nn.Conv1d, nn.Conv2d, nn.Conv3d]:
                    fused_layer = fuse_conv_bn_eval(first_layer, bn)
                else:  # nn.Linear
                    fused_layer = fuse_linear_bn_eval(first_layer, bn)
                replace_node_module(node.args[0], modules, fused_layer)
                node.replace_all_uses_with(node.args[0])
                new_graph.erase_node(node)
    return fx.GraphModule(fx_model, new_graph)