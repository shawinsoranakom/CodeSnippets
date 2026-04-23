def get_text_config(self, decoder=None, encoder=None) -> "PreTrainedConfig":
        """
        Returns the text config related to the text input (encoder) or text output (decoder) of the model. The
        `decoder` and `encoder` input arguments can be used to specify which end of the model we are interested in,
        which is useful on models that have both text input and output modalities.

        There are three possible outcomes of using this method:
        1. On most models, it returns the original config instance itself.
        2. On newer (2024+) composite models, it returns the text section of the config, which is nested under a set
            of valid names.
        3. On older (2023-) composite models, it discards decoder-only parameters when `encoder=True` and vice-versa.

        Args:
            decoder (`Optional[bool]`, *optional*):
                If set to `True`, then only search for decoder config names.
            encoder (`Optional[bool]`, *optional*):
                If set to `True`, then only search for encoder config names.
        """
        return_both = decoder == encoder  # both unset or both set -> search all possible names

        decoder_possible_text_config_names = ("decoder", "generator", "text_config")
        encoder_possible_text_config_names = ("text_encoder",)
        if return_both:
            possible_text_config_names = encoder_possible_text_config_names + decoder_possible_text_config_names
        elif decoder:
            possible_text_config_names = decoder_possible_text_config_names
        else:
            possible_text_config_names = encoder_possible_text_config_names

        valid_text_config_names = []
        for text_config_name in possible_text_config_names:
            if hasattr(self, text_config_name):
                text_config = getattr(self, text_config_name, None)
                if text_config is not None:
                    valid_text_config_names += [text_config_name]

        if len(valid_text_config_names) > 1:
            raise ValueError(
                f"Multiple valid text configs were found in the model config: {valid_text_config_names}. In this "
                "case, using `get_text_config()` would be ambiguous. Please specify the desired text config directly, "
                "e.g. `text_config = config.sub_config_name`"
            )
        elif len(valid_text_config_names) == 1:
            config_to_return = getattr(self, valid_text_config_names[0])
        else:
            config_to_return = self

        # handle legacy models with flat config structure, when we only want one of the configs
        if not return_both and len(valid_text_config_names) == 0 and config_to_return.is_encoder_decoder:
            config_to_return = copy.deepcopy(config_to_return)
            prefix_to_keep = "decoder" if decoder else "encoder"
            for key in config_to_return.to_dict():
                # NOTE: We can't discard keys because:
                # 1) we can't truly delete a cls attribte on a dataclass; 2) we can't set the value to `None` due to
                # strict validation. So we just keep it as is, since there are only a couple old models falling in this condition
                if key.startswith(prefix_to_keep):
                    # [encoder/decoder]_layers -> num_hidden_layers
                    if key == prefix_to_keep + "_layers":
                        new_key = "num_hidden_layers"
                    # [encoder/decoder]_attention_heads -> num_attention_heads
                    elif key == prefix_to_keep + "_attention_heads":
                        new_key = "num_attention_heads"
                    # e.g. encoder_hidden_act -> hidden_act
                    else:
                        new_key = key[len(prefix_to_keep) + 1 :]

                    # Does the class map the new key into a different attribute name at read time? if so, let's write
                    # into that attribute instead
                    if new_key in config_to_return.attribute_map:
                        new_key = config_to_return.attribute_map[new_key]

                    value = getattr(config_to_return, key)
                    delattr(config_to_return, key)
                    setattr(config_to_return, new_key, value)

        return config_to_return