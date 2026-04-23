def to_dict(self) -> dict[str, Any]:
        """
        Serializes this instance to a Python dictionary.

        Returns:
            `dict[str, Any]`: Dictionary of all the attributes that make up this configuration instance.
        """
        output = copy.deepcopy(self.__dict__)
        if hasattr(self.__class__, "model_type"):
            output["model_type"] = self.__class__.model_type

        # Transformers version when serializing the model
        output["transformers_version"] = __version__

        # Pop "kwargs" since they are unpacked and set in the post init
        output.pop("kwargs", None)

        def to_list(value):
            if isinstance(value, tuple):
                value = [to_list(item) for item in value]
            return value

        for key, value in output.items():
            # Deal with nested configs like CLIP
            if isinstance(value, PreTrainedConfig):
                value = value.to_dict()
                del value["transformers_version"]

            # Some models have defaults as tuples because dataclass
            # doesn't allow mutables. Let's convert back to `list``
            elif isinstance(value, tuple):
                value = to_list(value)

            output[key] = value

        self._remove_keys_not_serialized(output)

        if hasattr(self, "quantization_config"):
            output["quantization_config"] = (
                self.quantization_config.to_dict()
                if not isinstance(self.quantization_config, dict) and self.quantization_config is not None
                else self.quantization_config
            )
        self.dict_dtype_to_str(output)

        return output