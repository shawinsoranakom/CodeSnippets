def _classify_module_sharding(self, model: nn.Module):
        """
        Categorize modules based on their weight sharding requirements
        for tensor parallelism.
        """
        for name, module in model.named_modules():
            # Some modules like `ReplicatedLinear` should not have their weights
            # sharded. The reason for implementing it this way is to avoid new
            # static variable in the model implementation.
            if isinstance(module, (ReplicatedLinear,)):
                self.unsharded_weights_modules.append(name)
            # `QKVParallelLinear` and `MergedColumnParallelLinear` might have
            # fused weights on disk. We need to use the output sizes of these
            # modules to shard the weights correctly.
            elif isinstance(module, (QKVParallelLinear, MergedColumnParallelLinear)):
                self.maybe_fused_weights_modules[name] = module.output_sizes
            # In TP, these weights are partitioned along the column
            # dimension (dim=-1)
            elif isinstance(module, (RowParallelLinear,)):
                self.column_sharded_weights_modules.append(name)
            elif isinstance(module, FusedMoE):
                expert_mapping = self.expert_params_mapping
                for exp in expert_mapping:
                    if exp[-1] == "w2":
                        weight_name = exp[1]
                        rep_name = name.replace(
                            "experts", ""
                        ) + weight_name.removesuffix(".")
                        self.column_sharded_weights_modules.append(rep_name)