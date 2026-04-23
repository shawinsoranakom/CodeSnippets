def _set_return_timestamps(self, return_timestamps, is_shortform, generation_config):
        if return_timestamps is None and hasattr(generation_config, "return_timestamps"):
            return_timestamps = generation_config.return_timestamps

        if not is_shortform:
            if return_timestamps is False:
                raise ValueError(
                    "You have passed more than 3000 mel input features (> 30 seconds) which automatically "
                    "enables long-form generation which requires the model to predict timestamp tokens. Please "
                    "either pass `return_timestamps=True` or make sure to pass no more than 3000 mel input features."
                )

            logger.info("Setting `return_timestamps=True` for long-form generation.")
            return_timestamps = True

        if return_timestamps and not hasattr(generation_config, "no_timestamps_token_id"):
            raise ValueError(
                "You are trying to return timestamps, but the generation config is not properly set. "
                "Make sure to initialize the generation config with the correct attributes that are needed such as "
                "`no_timestamps_token_id`. For more details on how to generate the approtiate config, refer to "
                "https://github.com/huggingface/transformers/issues/21878#issuecomment-1451902363"
            )

        generation_config.return_timestamps = return_timestamps

        if hasattr(generation_config, "no_timestamps_token_id"):
            timestamp_begin = generation_config.no_timestamps_token_id + 1
        else:
            # BC for models missing the `no_timestamps_token_id` in the generation config when generating short-form
            # with no timestamps. We set the timestamp begin token larger than the vocab size, such that the
            # timestamp condition is never met in the decoding loop
            timestamp_begin = self.config.vocab_size + 1

        return timestamp_begin