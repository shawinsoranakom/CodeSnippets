def _convert_torchao_model(model):
    from transformers import TorchAoConfig
    from torchao.quantization import quantize_, ModuleFqnToConfig
    from torchao.quantization.qat import QATConfig
    from torchao.utils import TorchAOBaseTensor

    module_to_fqn_dict = {}
    for base_config, filter_fn in model._torchao_config.base_config_and_filter_fns:
        quantize_(model, QATConfig(base_config, step = "convert"), filter_fn = filter_fn)

        # Default filter function used for quantize_
        if filter_fn is None:
            if "_default" in module_to_fqn_dict:
                raise ValueError("Cannot use multiple default quantization configs")
            module_to_fqn_dict["_default"] = base_config
        else:
            for fqn in _filter_fn_to_fqns(model, filter_fn):
                if fqn in module_to_fqn_dict:
                    raise ValueError(f"Found multiple quantization configs for {fqn}")
                module_to_fqn_dict[fqn] = base_config

    in_emb = model.get_input_embeddings()
    out_proj = model.get_output_embeddings() or getattr(model, "lm_head", None)
    kwargs = {}
    if isinstance(in_emb.weight, TorchAOBaseTensor) or (
        out_proj is not None and isinstance(out_proj.weight, TorchAOBaseTensor)
    ):
        kwargs["include_input_output_embeddings"] = True
        kwargs["modules_to_not_convert"] = []

    quant_config = ModuleFqnToConfig(module_to_fqn_dict)
    quantization_config = TorchAoConfig(quant_type = quant_config, **kwargs)
    model.config.quantization_config = quantization_config