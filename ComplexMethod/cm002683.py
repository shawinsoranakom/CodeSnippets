def to_diff_dict(self) -> dict[str, Any]:
        """
        Removes all attributes from the configuration that correspond to the default config attributes for
        better readability, while always retaining the `config` attribute from the class. Serializes to a
        Python dictionary.

        Returns:
            dict[str, Any]: Dictionary of all the attributes that make up this configuration instance.
        """
        config_dict = self.to_dict()

        # Get the default config dict (from a fresh PreTrainedConfig instance)
        default_config_dict = PreTrainedConfig().to_dict()

        # get class specific config dict
        class_config_dict = self.__class__().to_dict() if not self.has_no_defaults_at_init else {}

        serializable_config_dict = {}

        # Only serialize values that differ from the default config,
        # except always keep the 'config' attribute.
        for key, value in config_dict.items():
            if (
                isinstance(getattr(self, key, None), PreTrainedConfig)
                and key in class_config_dict
                and isinstance(class_config_dict[key], dict)
            ):
                # For nested configs we need to clean the diff recursively
                diff = recursive_diff_dict(value, default_config_dict, config_obj=getattr(self, key, None))
                if "model_type" in value:
                    # Needs to be set even if it's not in the diff
                    diff["model_type"] = value["model_type"]

                serializable_config_dict[key] = diff
            elif (
                key not in default_config_dict
                or key == "transformers_version"
                or key == "vocab_file"
                or value != default_config_dict[key]
                or (key in default_config_dict and value != class_config_dict.get(key, value))
            ):
                serializable_config_dict[key] = value

        self._remove_keys_not_serialized(serializable_config_dict)

        # Key removed only in diff dict
        if "_name_or_path" in serializable_config_dict:
            del serializable_config_dict["_name_or_path"]

        if hasattr(self, "quantization_config"):
            serializable_config_dict["quantization_config"] = (
                self.quantization_config.to_dict()
                if not isinstance(self.quantization_config, dict) and self.quantization_config is not None
                else self.quantization_config
            )
        self.dict_dtype_to_str(serializable_config_dict)

        return serializable_config_dict