def __init__(self, *args, **kwargs):
        # First, extract chat template from kwargs. It can never be a positional arg
        setattr(self, "chat_template", kwargs.pop("chat_template", None))

        self.image_ids = [getattr(self, "image_token_id", None)]
        self.video_ids = [getattr(self, "video_token_id", None)]
        self.audio_ids = [getattr(self, "audio_token_id", None)]

        # Check audio tokenizer for its class but do not treat it as attr to avoid saving weights
        if (audio_tokenizer := kwargs.pop("audio_tokenizer", None)) is not None:
            proper_class = self.check_argument_for_proper_class("audio_tokenizer", audio_tokenizer)
            if not (is_torch_available() and isinstance(audio_tokenizer, PreTrainedAudioTokenizerBase)):
                raise ValueError(
                    f"Tried to use `{proper_class}` for audio tokenization. However, this class is not"
                    " registered for audio tokenization."
                )
            setattr(self, "audio_tokenizer", audio_tokenizer)

        # Sanitize args and kwargs
        for key in kwargs:
            if key not in self.get_attributes():
                raise TypeError(f"Unexpected keyword argument {key}.")
        for arg, attribute_name in zip(args, self.get_attributes()):
            if attribute_name in kwargs:
                raise TypeError(f"Got multiple values for argument {attribute_name}.")
            else:
                kwargs[attribute_name] = arg

        if len(kwargs) != len(self.get_attributes()):
            raise ValueError(
                f"This processor requires {len(self.get_attributes())} arguments: {', '.join(self.get_attributes())}. Got "
                f"{len(args)} arguments instead."
            )

        # Check each arg is of the proper class (this will also catch a user initializing in the wrong order)
        for attribute_name, arg in kwargs.items():
            self.check_argument_for_proper_class(attribute_name, arg)
            setattr(self, attribute_name, arg)