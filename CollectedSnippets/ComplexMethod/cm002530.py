def to_dict(self) -> dict[str, Any]:
        """
        Serializes this instance to a Python dictionary.

        Returns:
            `dict[str, Any]`: Dictionary of all the attributes that make up this processor instance.
        """
        # Exclude tokenizer attributes before deepcopying to avoid copying large vocab/token structures.
        tokenizer_attributes = set()
        for attribute in self.__class__.get_attributes():
            if attribute in self.__dict__:
                modality = _get_modality_for_attribute(attribute)
                if modality == "tokenizer":
                    tokenizer_attributes.add(attribute)

        dict_to_copy = {k: v for k, v in self.__dict__.items() if k not in tokenizer_attributes}
        output = copy.deepcopy(dict_to_copy)

        # Get the kwargs in `__init__`.
        sig = inspect.signature(self.__init__)
        # Only save the attributes that are presented in the kwargs of `__init__`.
        # or in the attributes
        attrs_to_save = list(sig.parameters) + self.__class__.get_attributes()
        # extra attributes to be kept
        attrs_to_save += ["auto_map"]

        if "chat_template" in output:
            del output["chat_template"]

        def cast_array_to_list(dictionary):
            """
            Numpy arrays are not serialiazable but can be in pre-processing dicts.
            This function casts arrays to list, recusring through the nested configs as well.
            """
            for key, value in dictionary.items():
                if isinstance(value, np.ndarray):
                    dictionary[key] = value.tolist()
                elif isinstance(value, dict):
                    dictionary[key] = cast_array_to_list(value)
            return dictionary

        # Special case, add `audio_tokenizer` dict which points to model weights and path
        if "audio_tokenizer" in output:
            audio_tokenizer_dict = {
                "audio_tokenizer_class": self.audio_tokenizer.__class__.__name__,
                "audio_tokenizer_name_or_path": self.audio_tokenizer.name_or_path,
            }
            output["audio_tokenizer"] = audio_tokenizer_dict

        # Serialize attributes as a dict
        output = {
            k: v.to_dict() if isinstance(v, PushToHubMixin) else v
            for k, v in output.items()
            if (
                k in attrs_to_save  # keep all attributes that have to be serialized
                and v.__class__.__name__ != "BeamSearchDecoderCTC"  # remove attributes with that are objects
            )
        }
        output = cast_array_to_list(output)
        output["processor_class"] = self.__class__.__name__

        return output