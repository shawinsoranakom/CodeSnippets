def _prepare_for_export(model, inputs_dict):
            # we don't test outputing a cache class for now
            inputs_dict.pop("use_cache", None)
            # we don't test loss computation for now
            inputs_dict.pop("return_loss", None)
            # we don't test loss computation for now
            inputs_dict.pop("future_values", None)

            # set experts implementation to batched_mm for export
            if model._can_set_experts_implementation():
                model.set_experts_implementation("batched_mm")

            # set attention implementation to sdpa for export
            if model._can_set_attn_implementation() and model.config.model_type != "videomae":
                try:
                    model.set_attn_implementation("sdpa")
                except Exception as e:
                    print(
                        f"Could not set attention implementation to sdpa for {model} of type {model.config.model_type} : {e}"
                    )

            for module in model.modules():
                if hasattr(module, "config"):
                    # disable cache usage for every submodel
                    if hasattr(module.config, "use_cache"):
                        module.config.use_cache = False
                    # disable returning loss for every submodel
                    if hasattr(module.config, "return_loss"):
                        module.config.return_loss = False
                    # disable mamba kernels for every submodel (mamba, jamba)
                    if hasattr(module.config, "use_mamba_kernels"):
                        module.config.use_mamba_kernels = False
                # disable classifier cast for nllb-moe
                if hasattr(module, "_cast_classifier"):
                    module._cast_classifier = lambda *args, **kwargs: None
                # disable mamba mask update for ssms
                if hasattr(module, "_update_mamba_mask"):
                    module._update_mamba_mask = lambda attention_mask, *args, **kwargs: attention_mask
                if hasattr(module, "_update_linear_attn_mask"):
                    module._update_linear_attn_mask = lambda attention_mask, *args, **kwargs: attention_mask

            return model, inputs_dict