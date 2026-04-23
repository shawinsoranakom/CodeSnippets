def convert(
        self,
        input_dict: dict[str, torch.Tensor],
        model: torch.nn.Module | None = None,
        full_layer_name: str | None = None,
        missing_keys=None,
        **kwargs,
    ) -> dict[str, torch.Tensor]:
        _, value = tuple(input_dict.items())[0]
        value = value[0] if isinstance(value, list) else value

        module, tensor_name = get_module_from_name(model, full_layer_name)

        module._parameters[tensor_name] = torch.nn.Parameter(value, requires_grad=value.requires_grad)
        # if we are quantizing tied parameters, to avoid tying the quantized weights
        # the correct order to do it is
        # 1. load the weight to model
        # 2. run tie_weights to populate the weights
        # 3. quantize
        input_embed = model.get_input_embeddings()
        is_embedding_param = id(module) == id(input_embed)
        untie_embedding_weights = self.hf_quantizer.quantization_config.untie_embedding_weights

        if untie_embedding_weights and is_embedding_param:
            setattr(model.config.get_text_config(decoder=True), "tie_word_embeddings", False)

        from torchao.quantization import FqnToConfig

        config = self.hf_quantizer.quantization_config.get_apply_tensor_subclass()
        if isinstance(config, FqnToConfig):
            module_fqn, top_level_param_name = full_layer_name.rsplit(".", 1)
            c = None
            if full_layer_name in config.fqn_to_config:
                assert not module_fqn.startswith("re:"), (
                    "param fqn should not start with`re:`, which is used for specifying regex"
                )
                c = config.module_fqn_to_config[full_layer_name]
            elif module_fqn in config.fqn_to_config:
                assert not module_fqn.startswith("re:"), (
                    "module fqn should not start with`re:`, which is used for specifying regex"
                )
                c = config.module_fqn_to_config[module_fqn]
            # regex match module and param
            else:
                for maybe_module_fqn_pattern in config.fqn_to_config:
                    # if key doesn't start with re, it is an exact fqn key, so we don't regex match
                    if not maybe_module_fqn_pattern.startswith("re:"):
                        continue
                    # see if param matches first
                    elif re.fullmatch(maybe_module_fqn_pattern[3:], full_layer_name):
                        c = config.module_fqn_to_config[maybe_module_fqn_pattern]
                        break
                    elif re.fullmatch(maybe_module_fqn_pattern[3:], module_fqn):
                        # we'll apply the config for first fully matched pattern
                        c = config.module_fqn_to_config[maybe_module_fqn_pattern]
                        break
                else:
                    c = config.module_fqn_to_config.get("_default", None)

            if c is not None:
                if top_level_param_name == "weight":
                    if is_embedding_param and untie_embedding_weights:
                        lm_head = module.weight.clone()
                    # we can apply the module config directly
                    self._quantize(module, c, (lambda x, fqn: True))
                    missing_keys.discard(full_layer_name)
                    module._is_hf_initialized = True
                    # torchao quantizes weights into a module but some models access the weight directly
                    # (e.g. module.o_proj.weight). The _is_hf_initialized flag is set at the module
                    # level only, so we also set it on each parameter to prevent _init_weights from
                    # calling normal_() on already-quantized Float8Tensors.
                    for param in module.parameters(recurse=False):
                        param._is_hf_initialized = True
                    return {"lm_head.weight": lm_head} if is_embedding_param and untie_embedding_weights else {}
                else:
                    # need to apply to custom param name
                    custom_param_fqn_config = FqnToConfig({top_level_param_name: c})
                    self._quantize(module, custom_param_fqn_config, filter_fn=None)
                    missing_keys.discard(full_layer_name)
                    module._is_hf_initialized = True
                    for param in module.parameters(recurse=False):
                        param._is_hf_initialized = True
                    return {}
            return {full_layer_name: value}

        if is_embedding_param and untie_embedding_weights:
            lm_head = module.weight.clone()
        self._quantize(module, self.hf_quantizer.quantization_config.get_apply_tensor_subclass())
        missing_keys.discard(full_layer_name)
        module._is_hf_initialized = True
        for param in module.parameters(recurse=False):
            param._is_hf_initialized = True
        return {"lm_head.weight": lm_head} if is_embedding_param and untie_embedding_weights else {}