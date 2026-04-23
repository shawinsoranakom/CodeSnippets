def patch_vit_for_tp(self, vit: torch.nn.Module, quant_config: QuantizationConfig):
        try:
            import timm
        except ImportError as e:
            raise ImportError("Please install timm") from e

        for name, module in vit.named_modules():
            if isinstance(module, nn.Linear):
                parent, attr_name = self._get_parent_and_attr(vit, name)
                if isinstance(parent, timm.layers.Mlp) and attr_name == "fc1":
                    new_linear = replace_linear_class(
                        module, "colwise", quant_config, prefix=name
                    )
                    setattr(parent, attr_name, new_linear)
                elif isinstance(parent, timm.layers.Mlp) and attr_name == "fc2":
                    new_linear = replace_linear_class(
                        module, "rowwise", quant_config, prefix=name
                    )
                    setattr(parent, attr_name, new_linear)

        return vit