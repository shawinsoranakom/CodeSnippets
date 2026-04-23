def update(self, defaults_only=False, allow_custom_entries=False, **kwargs):
        """
        Updates attributes of this class instance with attributes from `kwargs` if they match existing attributes,
        returning all the unused kwargs.

        Args:
            defaults_only (`bool`, *optional*, defaults to `False`):
                Whether to update all keys in config with `kwargs` or only those that are set to `None` (i.e. default value).
            allow_custom_entries (`bool`, *optional*, defaults to `False`):
                Whether to allow updating custom entries into the config with `kwargs` if not present in the current config.
            kwargs (`dict[str, Any]`):
                Dictionary of attributes to tentatively update this class.

        Returns:
            `dict[str, Any]`: Dictionary containing all the key-value pairs that were not used to update the instance.
        """
        to_remove = []
        for key, value in kwargs.items():
            if allow_custom_entries and not hasattr(self, key):
                setattr(self, key, value)
                to_remove.append(key)
            elif hasattr(self, key):
                if not defaults_only or getattr(self, key) is None:
                    setattr(self, key, value)
                    to_remove.append(key)

        # Confirm that the updated instance is still valid
        self.validate()

        # Remove all the attributes that were updated, without modifying the input dict
        unused_kwargs = {key: value for key, value in kwargs.items() if key not in to_remove}
        return unused_kwargs