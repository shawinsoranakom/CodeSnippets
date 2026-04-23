def llm_weights_generator():
            for name, w in weights:
                if is_vision_encoder_weights((name, w)):
                    if _is_layer_none_or_staged(self.vision_encoder):
                        continue
                    trimmed_name = ".".join(name.split(".")[1:])
                    for (
                        param_name,
                        weight_name,
                        shard_id,
                    ) in _vision_encoder_stacked_params:
                        if weight_name in trimmed_name:
                            trimmed_name = trimmed_name.replace(weight_name, param_name)
                            param = vision_encoder_dict[trimmed_name]
                            weight_loader = param.weight_loader
                            weight_loader(param, w, shard_id)
                            break
                    else:
                        for old, new in _vision_encoder_name_remap.items():
                            if old in trimmed_name:
                                trimmed_name = trimmed_name.replace(old, new)
                                break

                        param = vision_encoder_dict.get(trimmed_name)
                        if param is not None:
                            weight_loader = getattr(
                                param, "weight_loader", default_weight_loader
                            )
                            weight_loader(param, w)
                elif is_patch_merger((name, w)):
                    if _is_layer_none_or_staged(self.patch_merger):
                        continue
                    trimmed_name = ".".join(name.split(".")[1:])
                    param = patch_merger_dict[trimmed_name]
                    weight_loader = getattr(
                        param, "weight_loader", default_weight_loader
                    )
                    weight_loader(param, w)
                elif is_pre_mm_projector_norm((name, w)):
                    if _is_layer_none_or_staged(self.pre_mm_projector_norm):
                        continue
                    trimmed_name = ".".join(name.split(".")[1:])
                    param = pre_mm_projector_norm_dict[trimmed_name]
                    with torch.no_grad():
                        default_weight_loader(param, w)
                elif is_vision_lang_adapter_weights((name, w)):
                    if _is_layer_none_or_staged(self.vision_language_adapter):
                        continue
                    trimmed_name = ".".join(name.split(".")[1:])
                    param = vision_lang_adapter_dict.get(trimmed_name)
                    if param is not None:
                        weight_loader = getattr(
                            param, "weight_loader", default_weight_loader
                        )
                        weight_loader(param, w)
                else:
                    name = name.removeprefix("language_model.")
                    yield (name, w)