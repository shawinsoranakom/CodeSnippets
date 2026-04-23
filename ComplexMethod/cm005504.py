def delete_adapter(self, adapter_names: list[str] | str) -> None:
        """
        Delete a PEFT adapter from the underlying model.

        Args:
            adapter_names (`Union[list[str], str]`):
                The name(s) of the adapter(s) to delete.
        """

        check_peft_version(min_version=MIN_PEFT_VERSION)

        if not self._hf_peft_config_loaded:
            raise ValueError("No adapter loaded. Please load an adapter first.")

        from peft.functional import delete_adapter

        if isinstance(adapter_names, str):
            adapter_names = [adapter_names]

        # Check that all adapter names are present in the config
        missing_adapters = [name for name in adapter_names if name not in self.peft_config]
        if missing_adapters:
            raise ValueError(
                f"The following adapter(s) are not present and cannot be deleted: {', '.join(missing_adapters)}"
            )

        prefixes = [f"{self.peft_config[adapter_name].peft_type.value.lower()}_" for adapter_name in adapter_names]
        for adapter_name, prefix in zip(adapter_names, prefixes):
            delete_adapter(self, adapter_name=adapter_name, prefix=prefix)
            # For transformers integration - we need to pop the adapter from the config
            if getattr(self, "_hf_peft_config_loaded", False) and hasattr(self, "peft_config"):
                self.peft_config.pop(adapter_name, None)

        # In case all adapters are deleted, we need to delete the config
        # and make sure to set the flag to False
        if len(self.peft_config) == 0:
            del self.peft_config
            self._hf_peft_config_loaded = False