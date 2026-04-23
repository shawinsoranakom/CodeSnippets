def load_weights(self, weights) -> set[str]:
        loaded_params: set[str] = set()
        params_dict = dict(self.named_parameters())

        if isinstance(weights, dict):
            weights_list = list(weights.items())
        else:
            weights_list = list(weights)

        for name, weight in weights_list:
            if not name.startswith("radio_model."):
                # Skip non-radio weights
                continue

            sub = name[len("radio_model.") :]  # drop "radio_model." prefix

            # Skip buffers not used in vLLM
            if sub in {"summary_idxs"}:
                continue
            if sub.startswith("input_conditioner."):
                # we normalize in the input processor,
                # based on norm and std values from the config
                continue

            vllm_key = None
            if sub.startswith("model.patch_generator."):
                vllm_key = f"model.patch_generator.{sub.split('.', 2)[-1]}"
            elif sub.startswith("input_conditioner."):
                vllm_key = f"input_conditioner.{sub.split('.', 1)[-1]}"
            elif sub.startswith("model.blocks."):
                # Encoder blocks: HF 'model.blocks.{i}.' ->
                # vLLM 'model.encoder.layers.{i}.'
                parts = sub.split(".")
                if len(parts) >= 4:
                    layer_idx = parts[2]
                    suffix = ".".join(parts[3:])
                    # Skip layer-scale entries that vLLM doesn't use
                    if suffix in {"ls1", "ls2"} or suffix.startswith(("ls1.", "ls2.")):
                        continue
                    vllm_key = f"model.encoder.layers.{layer_idx}.{suffix}"

            if vllm_key and vllm_key in params_dict:
                param = params_dict[vllm_key]
                weight_loader = getattr(param, "weight_loader", default_weight_loader)
                weight_loader(param, weight)
                loaded_params.add(vllm_key)

        return loaded_params