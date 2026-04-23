def _get_logits_processor_kwargs(self, do_sample=False, config=None):
        logits_processor_kwargs = {
            "bad_words_ids": [[1, 0]],
            "repetition_penalty": 1.2,
            "remove_invalid_values": True,
        }
        if do_sample:
            logits_processor_kwargs.update(
                {
                    "top_k": 10,
                    "top_p": 0.7,
                    "temperature": 0.7,
                }
            )
        # TODO (joao, raushan): see this comment for a long-term fix
        # https://github.com/huggingface/transformers/pull/33593#issuecomment-2361824264)
        # This is a band-aid for VLM models, to ensure they don't generate image/video tokens which would cause them
        # to crash. On pretrained models this isn't a risk, as they are trained to not generate these tokens.
        if config is not None:
            for key in [
                "image_token_id",
                "video_token_id",
                "audio_token_id",
                "vision_start_token_id",
                "audio_start_token_id",
                "audio_end_token_id",
                "vision_end_token_id",
            ]:
                token_index = getattr(config, key, None)
                if token_index is None and hasattr(self, "model_tester"):
                    token_index = getattr(self.model_tester, key, None)
                if token_index is not None and token_index < config.get_text_config().vocab_size:
                    logits_processor_kwargs["bad_words_ids"].append([token_index])

        return logits_processor_kwargs