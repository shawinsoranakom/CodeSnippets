def _update_model_kwargs_for_generation(
        self,
        outputs: ModelOutput,
        model_kwargs: dict[str, Any],
        is_encoder_decoder: bool = False,
        num_new_tokens: int = 1,
    ) -> dict[str, Any]:
        """
        Update the model kwargs to account for the `num_new_tokens` new tokens that were just generated.
        That is, update the `attention_mask`, `position_ids`, and `token_type_ids` to account for the
        new tokens of the total sequence.
        Note that this function never slices inputs, this is performed in `prepare_inputs_for_generation`.
        """
        # update past_key_values keeping its naming used in model code
        for possible_cache_name in ALL_CACHE_NAMES:
            if possible_cache_name in outputs:
                # TODO (joao): remove output/input mismatch when these old models (xlnet, reformer) are deprecated
                if possible_cache_name in ("past_buckets_states", "mems"):
                    cache_name = "past_key_values"
                else:
                    cache_name = possible_cache_name
                model_kwargs[cache_name] = getattr(outputs, possible_cache_name)
                break

        # update token_type_ids with last value
        if (token_type_ids := model_kwargs.get("token_type_ids")) is not None:
            model_kwargs["token_type_ids"] = torch.cat([token_type_ids, token_type_ids[:, -num_new_tokens:]], dim=-1)

        # update mm_token_type_ids with zeros (only-text)
        if (mm_token_type_ids := model_kwargs.get("mm_token_type_ids")) is not None:
            model_kwargs["mm_token_type_ids"] = torch.cat(
                [mm_token_type_ids, mm_token_type_ids.new_zeros((mm_token_type_ids.shape[0], num_new_tokens))], dim=-1
            )

        # Position ids (2D or 3D sometimes)
        position_ids_key = "position_ids" if not is_encoder_decoder else "decoder_position_ids"
        if (position_ids := model_kwargs.get(position_ids_key)) is not None:
            # We want to expand to the same number of dims which is not always the same
            required_dim = [1] * (position_ids.dim() - 1) + [-1]
            next_position_ids = (
                torch.arange(num_new_tokens, dtype=position_ids.dtype, device=position_ids.device).view(*required_dim)
                + position_ids[..., -1:]
                + 1
            )
            next_position_ids = torch.cat([position_ids, next_position_ids], dim=-1)
            model_kwargs[position_ids_key] = next_position_ids

        # 2D attention mask (always 2D here)
        attention_mask_key = "attention_mask" if not is_encoder_decoder else "decoder_attention_mask"
        if (attention_mask := model_kwargs.get(attention_mask_key)) is not None:
            model_kwargs[attention_mask_key] = torch.cat(
                [attention_mask, attention_mask.new_ones((attention_mask.shape[0], num_new_tokens))], dim=-1
            )

        return model_kwargs