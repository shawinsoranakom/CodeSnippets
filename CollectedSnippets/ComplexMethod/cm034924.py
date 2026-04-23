def _prepare_decoder_input_ids_for_generation(
        self,
        batch_size,
        model_kwargs,
        decoder_start_token_id=None,
        bos_token_id=None,
    ):

        # 1. Check whether the user has defined `decoder_input_ids` manually. To facilitate in terms of input naming,
        # we also allow the user to pass it under `input_ids`, if the encoder does not use it as the main input.
        if model_kwargs is not None and "decoder_input_ids" in model_kwargs:
            decoder_input_ids = model_kwargs.pop("decoder_input_ids")
        elif "input_ids" in model_kwargs:
            decoder_input_ids = model_kwargs.pop("input_ids")
        else:
            decoder_input_ids = None

        # 2. Encoder-decoder models expect the `decoder_input_ids` to start with a special token. Let's ensure that.
        decoder_start_token_id = self._get_decoder_start_token_id(
            decoder_start_token_id, bos_token_id
        )

        if isinstance(decoder_start_token_id, list):
            if len(decoder_start_token_id) != batch_size:
                raise ValueError(
                    f"`decoder_start_token_id` expected to have length {batch_size} but got {len(decoder_start_token_id)}"
                )
            decoder_input_ids_start = paddle.to_tensor(
                decoder_start_token_id,
                dtype=paddle.int64,
            )
            decoder_input_ids_start = decoder_input_ids_start.view(-1, 1)
        else:
            use_parallel = self.config_decoder.use_parallel
            parallel_step = self.config_decoder.parallel_step

            if use_parallel:
                decoder_input_ids_start = (
                    paddle.ones(
                        (batch_size, parallel_step),
                        dtype=paddle.int64,
                    )
                    * decoder_start_token_id
                )
            else:
                decoder_input_ids_start = (
                    paddle.ones(
                        (batch_size, 1),
                        dtype=paddle.int64,
                    )
                    * decoder_start_token_id
                )
        # no user input -> use decoder_start_token_id as decoder_input_ids
        if decoder_input_ids is None:
            decoder_input_ids = decoder_input_ids_start
        # exception: Donut checkpoints have task-specific decoder starts and don't expect a BOS token
        elif (
            self.config.model_type == "vision-encoder-decoder"
            and "donut" in self.name_or_path.lower()
        ):
            pass
        elif self.config.model_type in ["whisper"]:
            pass
        # user input but doesn't start with decoder_start_token_id -> prepend decoder_start_token_id (and adjust
        # decoder_attention_mask if provided)
        elif (
            isinstance(decoder_start_token_id, int)
            and (decoder_input_ids[:, 0] != decoder_start_token_id).all().item()
        ) or (
            isinstance(decoder_start_token_id, paddle.Tensor)
            and (decoder_input_ids[:, 0] != decoder_start_token_id[:, 0]).all().item()
        ):
            decoder_input_ids = paddle.concat(
                [decoder_input_ids_start, decoder_input_ids], axis=-1
            )
            if "decoder_attention_mask" in model_kwargs:
                decoder_attention_mask = model_kwargs["decoder_attention_mask"]
                decoder_attention_mask = paddle.cat(
                    (
                        paddle.ones_like(decoder_attention_mask)[:, :1],
                        decoder_attention_mask,
                    ),
                    dim=-1,
                )
                model_kwargs["decoder_attention_mask"] = decoder_attention_mask

        return decoder_input_ids, model_kwargs