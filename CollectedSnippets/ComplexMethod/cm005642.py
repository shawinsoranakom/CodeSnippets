def _forward(self, model_inputs, **generate_kwargs):
        input_ids = model_inputs["input_ids"]
        attention_mask = model_inputs.get("attention_mask", None)
        # Allow empty prompts
        if input_ids.shape[1] == 0:
            input_ids = None
            attention_mask = None
            in_b = 1
        else:
            in_b = input_ids.shape[0]
        prompt_text = model_inputs.pop("prompt_text")

        # If there is a prefix, we may need to adjust the generation length. Do so without permanently modifying
        # generate_kwargs, as some of the parameterization may come from the initialization of the pipeline.
        prefix_length = generate_kwargs.pop("prefix_length", 0)
        if prefix_length > 0:
            has_max_new_tokens = "max_new_tokens" in generate_kwargs or (
                "generation_config" in generate_kwargs
                and generate_kwargs["generation_config"].max_new_tokens is not None
            )
            if not has_max_new_tokens:
                generate_kwargs["max_length"] = generate_kwargs.get("max_length") or self.generation_config.max_length
                generate_kwargs["max_length"] += prefix_length
            has_min_new_tokens = "min_new_tokens" in generate_kwargs or (
                "generation_config" in generate_kwargs
                and generate_kwargs["generation_config"].min_new_tokens is not None
            )
            if not has_min_new_tokens and "min_length" in generate_kwargs:
                generate_kwargs["min_length"] += prefix_length

        # User-defined `generation_config` passed to the pipeline call take precedence
        if "generation_config" not in generate_kwargs:
            generate_kwargs["generation_config"] = self.generation_config

        output = self.model.generate(input_ids=input_ids, attention_mask=attention_mask, **generate_kwargs)

        if isinstance(output, ModelOutput):
            generated_sequence = output.sequences
            other_outputs = {k: v for k, v in output.items() if k not in {"sequences", "past_key_values"}}
            out_b = generated_sequence.shape[0]

            for key, value in other_outputs.items():
                if isinstance(value, torch.Tensor) and value.shape[0] == out_b:
                    other_outputs[key] = value.reshape(in_b, out_b // in_b, *value.shape[1:])
                if isinstance(value, tuple) and len(value[0]) == out_b:
                    value = torch.stack(value).swapaxes(0, 1)
                    other_outputs[key] = value
        else:
            generated_sequence = output
            other_outputs = {}

        out_b = generated_sequence.shape[0]
        generated_sequence = generated_sequence.reshape(in_b, out_b // in_b, *generated_sequence.shape[1:])

        model_outputs = {
            "generated_sequence": generated_sequence,
            "input_ids": input_ids,
            "prompt_text": prompt_text,
        }
        if other_outputs:
            model_outputs.update({"additional_outputs": other_outputs})
        return model_outputs