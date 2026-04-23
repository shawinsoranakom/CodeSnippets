def _recursive_replace(module: nn.Module, prefix: str):
            for child_name, child_module in module.named_children():
                new_module = child_module
                qual_name = maybe_prefix(prefix, child_name)
                if (
                    isinstance(module, nn.ModuleList)
                    and len(module) == self.text_config.num_hidden_layers
                ):
                    # Populate Eagle3 attrs
                    self._target_class = type(child_module)
                    layer_name = qual_name.removeprefix("model.")
                    self._layer_names[int(child_name)] = layer_name
                    # MTP weights should not be loaded into the base model
                    num_hidden_layers = self.text_config.num_hidden_layers
                    names = (
                        "n_predict",  # Override from SpeculativeConfig
                        "num_nextn_predict_layers",  # Most models
                        "mtp_num_hidden_layers",  # Qwen 3.5
                    )
                    n_predict = getattr_iter(self.text_config, names, 0)
                    for i in range(num_hidden_layers, num_hidden_layers + n_predict):
                        mtp_prefix = f"{prefix}.{i}."
                        if mtp_prefix not in self.ignore_unexpected_prefixes:
                            self.ignore_unexpected_prefixes.append(mtp_prefix)
                # Replace modules as needed
                if isinstance(child_module, nn.Linear):
                    generator = (p for p in tp_plan if re.match(p, qual_name))
                    pattern = next(generator, None)
                    # Some weight loaders expect all linear layers to inherit
                    # LinearBase, so we set a default style which causes any
                    # unspecified layers to be replaced with ReplicatedLinear
                    style = tp_plan.get(pattern, "replicate")
                    new_module = replace_linear_class(
                        child_module, style, self.quant_config, prefix=qual_name
                    )
                elif isinstance(child_module, (nn.Conv2d, nn.Conv3d)):
                    new_module = replace_conv_class(child_module)
                elif child_module.__class__.__name__.endswith("RMSNorm"):
                    new_module = replace_rms_norm_class(
                        child_module, self.text_config.hidden_size
                    )
                else:
                    _recursive_replace(child_module, prefix=qual_name)

                if new_module is not child_module:
                    setattr(module, child_name, new_module)
                    log_replacement(qual_name, child_module, new_module)