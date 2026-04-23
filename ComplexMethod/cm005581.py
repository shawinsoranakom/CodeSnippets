def param_needs_quantization(self, model: "PreTrainedModel", param_name: str, **kwargs) -> bool:
        # check if the param_name is not in self.modules_to_not_convert
        if not should_convert_module(param_name, self.modules_to_not_convert):
            return False

        # we only quantize the weight of nn.Linear and nn.Embedding
        module, tensor_name = get_module_from_name(model, param_name)
        _QUANTIZABLE = [torch.nn.Linear]
        if self.quantization_config.include_input_output_embeddings:
            _QUANTIZABLE.append(torch.nn.Embedding)

        from torchao.quantization import FqnToConfig, fqn_matches_fqn_config

        if isinstance(self.quantization_config.quant_type, FqnToConfig):
            module_fqn, _ = param_name.rsplit(".", 1)
            if (
                fqn_matches_fqn_config(module_fqn, self.quantization_config.quant_type)
                or fqn_matches_fqn_config(param_name, self.quantization_config.quant_type)
                or (
                    "_default" in self.quantization_config.quant_type.fqn_to_config
                    and isinstance(module, tuple(_QUANTIZABLE))
                )
            ):
                return True

        return isinstance(module, tuple(_QUANTIZABLE)) and tensor_name == "weight"