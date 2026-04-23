def load_weights(self, weights: Iterable[tuple[str, torch.Tensor]]):
        adapter_dict = dict(self.mlp1.named_parameters())

        def is_llm(name: str) -> bool:
            return name.startswith("language_model")

        def is_adapter_weights(weight: tuple[str, torch.Tensor]):
            return weight[0].startswith("mlp1")

        def is_vision_weights(name: str) -> bool:
            return name.startswith("vision_model.radio_model.")

        def is_sound_weights(name: str) -> bool:
            return name.startswith("sound")

        # Separate weights by component
        llm_weights = []
        vision_weights = []
        sound_weights = []

        for name, w in weights:
            if is_llm(name):
                # Strip 'language_model.' prefix for LLM weights
                llm_weights.append((".".join(name.split(".")[1:]), w))
            elif is_adapter_weights((name, w)):
                # Load vision-language adapter weights directly
                trimmed_name = ".".join(name.split(".")[1:])
                param = adapter_dict[trimmed_name]
                with torch.no_grad():
                    default_weight_loader(param, w)
            elif is_vision_weights(name):
                # Convert: vision_model.radio_model.* → radio_model.*
                hf_key = name[len("vision_model.") :]  # Remove "vision_model." prefix
                vision_weights.append((hf_key, w))
            elif is_sound_weights(name):
                assert self.sound_encoder is not None
                sound_weights.append((name, w))

        self.language_model.load_weights(llm_weights)
        self.vision_model.load_weights(vision_weights)
        if self.sound_encoder is not None and len(sound_weights) > 0:
            self.sound_encoder.load_weights(sound_weights)