def load_weights(self, weights: Iterable[tuple[str, torch.Tensor]]) -> set[str]:
        stacked_params_mapping = [
            # (param_name, shard_name, shard_id)
            (".first_sub_layer.qkv_proj", ".first_sub_layer.query_net", "q"),
            (".first_sub_layer.qkv_proj", ".first_sub_layer.key_net", "k"),
            (".first_sub_layer.qkv_proj", ".first_sub_layer.value_net", "v"),
            (".second_sub_layer.kv_proj", ".second_sub_layer.key_net", "k"),
            (".second_sub_layer.kv_proj", ".second_sub_layer.value_net", "v"),
        ]
        params_dict = dict(self.named_parameters())
        buffers_dict = dict(self.named_buffers())
        params_dict.update(buffers_dict)

        loaded_params: set[str] = set()
        for name, loaded_weight in weights:
            for param_name, weight_name, shard_id in stacked_params_mapping:
                if weight_name not in name:
                    continue
                name = name.replace(weight_name, param_name)
                # Skip loading extra bias for GPTQ models.
                # if name.endswith(".bias") and name not in params_dict:
                #     continue

                param = params_dict[name]
                weight_loader = param.weight_loader
                weight_loader(param, loaded_weight, shard_id)
                break
            else:
                # Skip loading extra bias for GPTQ models.
                if name.endswith(".bias") and name not in params_dict:
                    continue

                param = params_dict[name]
                weight_loader = getattr(param, "weight_loader", default_weight_loader)

                # Convert buffer dtype to match loaded weight for pos_bias tensors
                if "pos_bias" in name and param.dtype != loaded_weight.dtype:
                    logger.info(
                        "Converting buffer %s dtype from %s to %s for loading.",
                        name,
                        param.dtype,
                        loaded_weight.dtype,
                    )
                    param.data = param.data.to(loaded_weight.dtype)

                weight_loader(param, loaded_weight)
            loaded_params.add(name)
        return loaded_params