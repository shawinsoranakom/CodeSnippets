def _check_and_maybe_initialize_inputs(
        self,
        input_ids=None,
        user_input_values=None,
        user_audio_codes=None,
        moshi_input_values=None,
        moshi_audio_codes=None,
        inputs_embeds=None,
        concat_unconditional_inputs=None,
    ):
        inputs = input_ids if inputs_embeds is None else inputs_embeds
        user_input = user_audio_codes if user_input_values is None else user_input_values
        moshi_input = moshi_audio_codes if moshi_input_values is None else moshi_input_values

        one_input_has_been_passed = (user_input is not None) or (moshi_input is not None) or (inputs is not None)

        # concat_unconditional_inputs will be False if inputs_embeds is used
        concat_unconditional_inputs = concat_unconditional_inputs and not (
            inputs_embeds is not None and input_ids is None
        )

        # if one or two of the three required inputs have been passed, throws an error
        if one_input_has_been_passed and (user_input is None):
            raise ValueError(
                "No user audio inputs have been passed alongside the other inputs. Make sure either `user_input_values` or `user_audio_codes` is passed or use `MoshiForConditionalGeneration.get_unconditional_inputs`. Check the `MoshiForConditionalGeneration` docstrings for more information."
            )
        elif one_input_has_been_passed and (moshi_input is None):
            raise ValueError(
                "No Moshi audio inputs have been passed alongside the other inputs. Make sure either `moshi_input_values` or `moshi_audio_codes` is passed or use `MoshiForConditionalGeneration.get_unconditional_inputs`. Check the `MoshiForConditionalGeneration` docstrings for more information."
            )
        elif one_input_has_been_passed and (inputs is None):
            raise ValueError(
                "No `input_ids` or `inputs_embeds` have been passed alongside the other inputs. Make sure `input_ids` is passed or use `MoshiForConditionalGeneration.get_unconditional_inputs`. Check the `MoshiForConditionalGeneration` docstrings for more information."
            )
        elif not one_input_has_been_passed:
            # if no inputs have been passed, use default values
            unconditional_inputs = self.get_unconditional_inputs()
            input_ids = unconditional_inputs.input_ids
            user_audio_codes = unconditional_inputs.user_audio_codes
            moshi_audio_codes = unconditional_inputs.moshi_audio_codes

            # in that case, no need to concat unconditional inputs
            concat_unconditional_inputs = False
        else:
            # check if same sequence length
            user_seq_length = user_input.shape[-1]
            moshi_seq_length = moshi_input.shape[-1]
            tokens_seq_length = inputs.shape[1]

            ratio = self.config.audio_encoder_config.frame_rate / self.config.sampling_rate
            moshi_seq_length = math.ceil(moshi_seq_length * ratio) if moshi_audio_codes is None else moshi_seq_length
            user_seq_length = math.ceil(user_seq_length * ratio) if user_audio_codes is None else user_seq_length

            if tokens_seq_length != moshi_seq_length or tokens_seq_length != user_seq_length:
                raise ValueError(
                    "At least one of the 3 inputs of `MoshiForConditionalGeneration` doesn't have the same sequence length as the others."
                    "Make sure that they all have the same sequence length. Check the `MoshiForConditionalGeneration` docstrings for more information."
                )

        return input_ids, user_audio_codes, moshi_audio_codes, concat_unconditional_inputs