def prepare_config_and_inputs_for_generate(self, batch_size=2):
        config, inputs_dict = self.model_tester.prepare_config_and_inputs_for_common()

        # We don't want a few model inputs in our model input dictionary for generation tests
        input_keys_to_ignore = [
            # we don't want to mask attention heads
            # we don't want encoder-decoder models to start from filled decoder ids
            "decoder_input_ids",
            "decoder_attention_mask",
            # we'll set cache use in each test differently
            "use_cache",
            # Ignore labels if it is in the input dict
            "labels",
            # model-specific exceptions should overload/overwrite this function
        ]

        # The diff from the general `prepare_config_and_inputs_for_generate` lies here
        patch_size = config.vision_config.patch_size
        num_patches_per_image = (self.model_tester.image_size**2) // (patch_size**2)
        num_grids_per_sample = 2  # 1 source + 1 target

        filtered_inputs_dict = {
            k: v[:batch_size, ...]
            if isinstance(v, torch.Tensor) and k not in ["pixel_values", "image_grid_thw", "images_per_sample"]
            else v
            for k, v in inputs_dict.items()
            if k not in input_keys_to_ignore
        }
        # pixel_values: each sample has 1 source image
        filtered_inputs_dict["pixel_values"] = inputs_dict["pixel_values"][: batch_size * num_patches_per_image]
        # image_grid_thw: each sample has 2 grids (1 source + 1 target)
        filtered_inputs_dict["image_grid_thw"] = inputs_dict["image_grid_thw"][: batch_size * num_grids_per_sample]
        # images_per_sample: each sample has 2 images
        filtered_inputs_dict["images_per_sample"] = torch.tensor(
            [num_grids_per_sample] * batch_size, device=torch_device
        )

        # It is important set `eos_token_id` to `None` to avoid early stopping (would break for length-based checks)
        text_gen_config = config.get_text_config(decoder=True)
        if text_gen_config.eos_token_id is not None and text_gen_config.pad_token_id is None:
            text_gen_config.pad_token_id = (
                text_gen_config.eos_token_id
                if isinstance(text_gen_config.eos_token_id, int)
                else text_gen_config.eos_token_id[0]
            )
        text_gen_config.eos_token_id = None
        text_gen_config.forced_eos_token_id = None

        return config, filtered_inputs_dict