def fuse_conv_bn(gm: torch.fx.GraphModule, inplace=False) -> torch.fx.GraphModule:
    """
    Fuses Convolution/BN layers for inference purposes.
    """
    modules_patterns = [
        (torch.nn.Conv1d, torch.nn.BatchNorm1d),
        (torch.nn.Conv2d, torch.nn.BatchNorm2d),
        (torch.nn.Conv3d, torch.nn.BatchNorm3d),
    ]
    module_function_patterns = [
        (torch.nn.Conv1d, F.batch_norm),
        (torch.nn.Conv2d, F.batch_norm),
        (torch.nn.Conv3d, F.batch_norm),
    ]
    modules = dict(gm.named_modules())

    class ConvBNFusion:
        def __init__(
            self,
            bn_node,
            conv_module,
            bn_module=None,  # For BN Module
            bn_running_mean=None,  # For Functional BN
            bn_running_var=None,
            bn_eps=None,
            bn_weight=None,
            bn_bias=None,
        ) -> None:
            self.bn_nodes = [
                bn_node,
            ]
            self.conv_module = conv_module
            self.bn_module = bn_module
            self.bn_running_mean = bn_running_mean
            self.bn_running_var = bn_running_var
            self.bn_eps = bn_eps
            self.bn_weight = bn_weight
            self.bn_bias = bn_bias
            self.fusion_enabled = True

        def add_bn_node(self, bn_node):
            self.bn_nodes.append(bn_node)

        def disable_fusion(self):
            self.fusion_enabled = False

        def is_fusion_enabled(self):
            return self.fusion_enabled

    conv_bn_to_fuse: dict[int, ConvBNFusion] = {}
    for pattern in modules_patterns:
        conv_bn_to_fuse.clear()
        for node in gm.graph.nodes:
            if matches_module_pattern(pattern, node, modules):
                if len(node.args[0].users) > 1:  # Output of conv is used by other nodes
                    continue
                conv = modules[node.args[0].target]
                bn = modules[node.target]
                eval_mode = all(not n.training for n in [conv, bn])
                if not eval_mode:
                    continue
                if not bn.track_running_stats:
                    continue

                # Do hash based on the module name of conv
                hash_id = hash(node.args[0].target)
                if hash_id not in conv_bn_to_fuse:
                    conv_bn_to_fuse[hash_id] = ConvBNFusion(node, conv, bn)
                else:
                    if bn == conv_bn_to_fuse[hash_id].bn_module:
                        # Do fusion if same bn module
                        conv_bn_to_fuse[hash_id].add_bn_node(node)
                    else:
                        # Disable the conv bn folding if conv shared by different bn
                        conv_bn_to_fuse[hash_id].disable_fusion()

        for conv_bn_fusion in conv_bn_to_fuse.values():
            if conv_bn_fusion.is_fusion_enabled():
                bn_nodes = conv_bn_fusion.bn_nodes
                conv = conv_bn_fusion.conv_module
                bn = conv_bn_fusion.bn_module

                # pyrefly: ignore [bad-argument-type]
                fused_conv = fuse_conv_bn_eval(conv, bn)
                for bn_node in bn_nodes:
                    replace_node_module(bn_node.args[0], modules, fused_conv)
                    bn_node.replace_all_uses_with(bn_node.args[0])
                    gm.graph.erase_node(bn_node)

    gm.graph.lint()
    for pattern in module_function_patterns:
        conv_bn_to_fuse.clear()
        for node in gm.graph.nodes:
            if matches_module_function_pattern(pattern, node, modules):
                # TODO: support kwargs.
                if len(node.args) != 8:
                    continue
                conv = modules[node.args[0].target]
                bn_training = node.args[5]
                bn_eps = node.args[7]
                if conv.training or bn_training:
                    continue
                if type(bn_eps) is not float:
                    continue

                def _used_by_same_conv_module(users):
                    conv_module_name = users[0].args[0].target
                    return all(
                        conv_module_name == user.args[0].target for user in users
                    )

                bn_args_is_constant = all(
                    n.op == "get_attr"
                    and (len(n.users) == 1 or _used_by_same_conv_module(list(n.users)))
                    for n in node.args[1:5]
                )
                if not bn_args_is_constant:
                    continue
                bn_running_mean = fetch_attr(node.args[1].target, gm)
                bn_running_var = fetch_attr(node.args[2].target, gm)
                bn_weight = fetch_attr(node.args[3].target, gm)
                bn_bias = fetch_attr(node.args[4].target, gm)
                if bn_running_mean is None or bn_running_var is None:
                    continue

                # Do hash based on the module name of conv
                hash_id = hash(node.args[0].target)
                if hash_id not in conv_bn_to_fuse:
                    conv_bn_to_fuse[hash_id] = ConvBNFusion(
                        node,
                        conv,
                        bn_running_mean=bn_running_mean,
                        bn_running_var=bn_running_var,
                        bn_eps=bn_eps,
                        bn_weight=bn_weight,
                        bn_bias=bn_bias,
                    )
                else:
                    if (
                        hash(bn_running_mean)
                        == hash(conv_bn_to_fuse[hash_id].bn_running_mean)
                        and hash(bn_running_var)
                        == hash(conv_bn_to_fuse[hash_id].bn_running_var)
                        and torch.allclose(
                            torch.tensor(bn_eps),
                            torch.tensor(conv_bn_to_fuse[hash_id].bn_eps),
                        )
                        and hash(bn_weight) == hash(conv_bn_to_fuse[hash_id].bn_weight)
                        and hash(bn_bias) == hash(conv_bn_to_fuse[hash_id].bn_bias)
                    ):
                        # Do fusion if same functional bn
                        conv_bn_to_fuse[hash_id].add_bn_node(node)
                    else:
                        # Disable the conv bn folding if conv shared by different bn
                        conv_bn_to_fuse[hash_id].disable_fusion()

        for conv_bn_fusion in conv_bn_to_fuse.values():
            if conv_bn_fusion.is_fusion_enabled():
                bn_nodes = conv_bn_fusion.bn_nodes
                conv = conv_bn_fusion.conv_module
                bn_running_mean = conv_bn_fusion.bn_running_mean
                bn_running_var = conv_bn_fusion.bn_running_var
                bn_eps = conv_bn_fusion.bn_eps
                bn_weight = conv_bn_fusion.bn_weight
                bn_bias = conv_bn_fusion.bn_bias

                fused_conv = copy.deepcopy(conv)
                fused_conv.weight, fused_conv.bias = fuse_conv_bn_weights(
                    fused_conv.weight,
                    fused_conv.bias,
                    # pyrefly: ignore [bad-argument-type]
                    bn_running_mean,
                    # pyrefly: ignore [bad-argument-type]
                    bn_running_var,
                    # pyrefly: ignore [bad-argument-type]
                    bn_eps,
                    bn_weight,
                    bn_bias,
                )
                for bn_node in bn_nodes:
                    replace_node_module(bn_node.args[0], modules, fused_conv)
                    bn_node.replace_all_uses_with(bn_node.args[0])
                    gm.graph.erase_node(bn_node)
    gm.graph.lint()
    gm.recompile()

    return gm