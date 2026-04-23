def _prepare_decoder_input_ids_for_generation(
            self,
            batch_size,
            model_kwargs,
            decoder_start_token_id=None,
            bos_token_id=None,
    ):
        if model_kwargs is not None and "decoder_input_ids" in model_kwargs:
            decoder_input_ids = model_kwargs.pop("decoder_input_ids")
        elif "input_ids" in model_kwargs:
            decoder_input_ids = model_kwargs.pop("input_ids")
        else:
            decoder_input_ids = None

        decoder_start_token_id = self._get_decoder_start_token_id(
            decoder_start_token_id, bos_token_id
        )

        if isinstance(decoder_start_token_id, list):
            if len(decoder_start_token_id) != batch_size:
                raise ValueError(
                    f"`decoder_start_token_id` expected to have length {batch_size} but got {len(decoder_start_token_id)}"
                )
            decoder_input_ids_start = torch.LongTensor(decoder_start_token_id)
            decoder_input_ids_start = decoder_input_ids_start.view(-1, 1)
        else:
            decoder_input_ids_start = (
                    torch.ones(
                        (batch_size, 1),
                        dtype=torch.int64,
                    )
                    * decoder_start_token_id
            )

        if decoder_input_ids is None:
            decoder_input_ids = decoder_input_ids_start
        elif (
                self.config.model_type == "vision-encoder-decoder"
                and "donut" in self.name_or_path.lower()
        ):
            pass
        elif self.config.model_type in ["whisper"]:
            pass
        elif (
                isinstance(decoder_start_token_id, int)
                and (decoder_input_ids[:, 0] != decoder_start_token_id).all().item()
        ) or (
                isinstance(decoder_start_token_id, torch.Tensor)
                and (decoder_input_ids[:, 0] != decoder_start_token_id[:, 0]).all().item()
        ):
            decoder_input_ids = torch.concat(
                [decoder_input_ids_start, decoder_input_ids], dim=-1
            )
            if "decoder_attention_mask" in model_kwargs:
                decoder_attention_mask = model_kwargs["decoder_attention_mask"]
                decoder_attention_mask = torch.cat(
                    (
                        torch.ones_like(decoder_attention_mask)[:, :1],
                        decoder_attention_mask,
                    ),
                    dim=-1,
                )
                model_kwargs["decoder_attention_mask"] = decoder_attention_mask

        return decoder_input_ids, model_kwargs