def from_dict(
        cls: type[SpecificPreTrainedConfigType], config_dict: dict[str, Any], **kwargs
    ) -> SpecificPreTrainedConfigType:
        """
        Instantiates a [`PreTrainedConfig`] from a Python dictionary of parameters.

        Args:
            config_dict (`dict[str, Any]`):
                Dictionary that will be used to instantiate the configuration object. Such a dictionary can be
                retrieved from a pretrained checkpoint by leveraging the [`~PreTrainedConfig.get_config_dict`] method.
            kwargs (`dict[str, Any]`):
                Additional parameters from which to initialize the configuration object.

        Returns:
            [`PreTrainedConfig`]: The configuration object instantiated from those parameters.
        """
        return_unused_kwargs = kwargs.pop("return_unused_kwargs", False)

        # The commit hash might have been updated in the `config_dict`, we don't want the kwargs to erase that update.
        if "_commit_hash" in kwargs and "_commit_hash" in config_dict:
            kwargs.setdefault("_commit_hash", config_dict["_commit_hash"])

        # To remove arg here are those passed along for our internal telemetry but we still need to remove them
        to_remove = ["_from_auto", "_from_pipeline"]
        valid_fields = [
            "num_labels",
            "attn_implementation",
            "experts_implementation",
            "output_attentions",
            "torch_dtype",
            "dtype",
            "name_or_path",
        ]
        for key, value in kwargs.items():
            if key in valid_fields:
                if key not in ["torch_dtype", "dtype"]:
                    config_dict[key] = value
                    to_remove.append(key)
                elif value != "auto":
                    config_dict[key] = value

        config = cls(**config_dict)

        for key, value in kwargs.items():
            if hasattr(config, key):
                current_attr = getattr(config, key)
                # To authorize passing a custom subconfig as kwarg in models that have nested configs.
                # We need to update only custom kwarg values instead and keep other attr in subconfig.
                if isinstance(current_attr, PreTrainedConfig) and isinstance(value, dict):
                    current_attr_updated = current_attr.to_dict()
                    current_attr_updated.update(value)
                    value = current_attr.__class__(**current_attr_updated)
                setattr(config, key, value)
                to_remove.append(key)

        for key in to_remove:
            kwargs.pop(key, None)

        logger.info(f"Model config {config}")
        if return_unused_kwargs:
            return config, kwargs
        else:
            return config