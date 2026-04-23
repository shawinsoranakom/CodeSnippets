def load_weights(self, weights: Iterable[tuple[str, torch.Tensor]]) -> set[str]:
        loaded_params: set[str] = set()
        params_dict = dict(self.named_parameters())
        buffers_dict = dict(self.named_buffers())

        if isinstance(weights, dict):
            weights_list = list(weights.items())
        else:
            weights_list = list(weights)

        for name, weight in weights_list:
            if name.startswith("sound_encoder.encoder.feature_extractor."):
                # Feature extractor buffers are handled outside the encoder.
                continue
            if name.startswith("sound_encoder."):
                target_name = name[len("sound_encoder.") :]
            elif name.startswith("sound_projection."):
                target_name = f"projection.{name[len('sound_projection.') :]}"
            else:
                continue

            target = params_dict.get(target_name)
            if target is None:
                target = buffers_dict.get(target_name)
            if target is None:
                if self._can_skip_missing_named_param(target_name):
                    continue
                raise ValueError(f"Unknown weight: {name}")
            weight_loader = getattr(target, "weight_loader", default_weight_loader)
            with torch.no_grad():
                weight_loader(target, weight)
            loaded_params.add(target_name)

        return loaded_params