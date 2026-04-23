def load_weights(self, weights: Iterable[tuple[str, torch.Tensor]]) -> set[str]:
        params_list = []
        model_buffers = dict(self.named_buffers())
        loaded_buffers = []
        for key, value in weights:
            if isinstance(value, (dict, OrderedDict)):
                if key == "state_dict":
                    weights_to_parse = value
                    for name, weight in weights_to_parse.items():
                        name = f"inference_runner.{name}"

                        if "pos_embed" in name:
                            continue

                        if "_timm_module." in name:
                            name = name.replace("_timm_module.", "")

                        # this model requires a couple of buffers to be loaded
                        # that are not loadable with the AutoWeightsLoader
                        if name in model_buffers:
                            if "_timm_module." in name:
                                name = name.replace("_timm_module.", "")
                            buffer = model_buffers[name]
                            weight_loader = getattr(
                                buffer, "weight_loader", default_weight_loader
                            )
                            weight_loader(buffer, weight)
                            loaded_buffers.append(name)
                        else:
                            params_list.append((name, weight))
                    break

            elif isinstance(value, torch.Tensor):
                params_list.append((f"inference_runner.model.{key}", value))

        # Load the remaining model parameters
        loader = AutoWeightsLoader(self)
        autoloaded_weights = loader.load_weights(params_list)

        return autoloaded_weights.union(set(loaded_buffers))