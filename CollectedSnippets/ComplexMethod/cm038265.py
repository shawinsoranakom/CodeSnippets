def _recursive_replace(module: nn.Module, prefix: str):
            for child_name, child_module in module.named_children():
                qual_name = maybe_prefix(prefix, child_name)
                # Naive implementations will have experts as ModuleList
                is_modulelist = isinstance(child_module, nn.ModuleList)
                # Packed implementations will have experts as 3D tensors of shapes like:
                # gate_up_proj = (num_experts, 2 * intermediate_size, hidden_size)
                # down_proj = (num_experts, intermediate_size, hidden_size)
                params = list(child_module.parameters())
                is_3d = len(params) > 0 and all(p.ndim == 3 for p in params)
                if child_name == "experts" and (is_modulelist or is_3d):
                    # Alias for readability
                    mlp = module
                    experts = child_module
                    # Do the experts have biases
                    has_bias = False
                    for experts_param_name, _ in experts.named_parameters():
                        if "bias" in experts_param_name:
                            has_bias = True
                            break
                    # If the config does not specify num_shared_experts, but
                    # the model has shared experts, we assume there is one.
                    if self.num_shared_experts == 0:
                        for mlp_param_name, _ in mlp.named_parameters():
                            if "shared_expert" in mlp_param_name:
                                self.num_shared_experts = 1
                                break
                    # Replace experts module with FusedMoE
                    fused_experts = TransformersFusedMoE(
                        num_experts=num_experts,
                        top_k=top_k,
                        hidden_size=hidden_size,
                        intermediate_size=intermediate_size,
                        renormalize=renormalize,
                        # Hard coded because topk happens in Transformers
                        use_grouped_topk=False,
                        num_expert_group=num_expert_group,
                        topk_group=topk_group,
                        quant_config=self.quant_config,
                        prefix=qual_name,
                        activation=activation,
                        enable_eplb=enable_eplb,
                        num_redundant_experts=num_redundant_experts,
                        has_bias=has_bias,
                        expert_mapping=expert_mapping,
                    )
                    mlp.experts = fused_experts
                    log_replacement(qual_name, experts, fused_experts)
                    # Update MixtureOfExperts mixin state
                    self.mlp_moe_layers.append(mlp)
                    self.moe_layers.append(fused_experts)
                    self.expert_weights.append(fused_experts.get_expert_weights())
                    self.num_moe_layers += 1
                else:
                    _recursive_replace(child_module, prefix=qual_name)