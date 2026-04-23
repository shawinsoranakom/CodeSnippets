def set_adapter(self, adapter_name: list[str] | str) -> None:
        """
        If you are not familiar with adapters and PEFT methods, we invite you to read more about them on the PEFT
        official documentation: https://huggingface.co/docs/peft

        Sets a specific adapter by forcing the model to use a that adapter and disable the other adapters.

        Args:
            adapter_name (`Union[list[str], str]`):
                The name of the adapter to set. Can be also a list of strings to set multiple adapters.
        """
        check_peft_version(min_version=MIN_PEFT_VERSION)
        if not self._hf_peft_config_loaded:
            raise ValueError("No adapter loaded. Please load an adapter first.")
        elif isinstance(adapter_name, list):
            missing = set(adapter_name) - set(self.peft_config)
            if len(missing) > 0:
                raise ValueError(
                    f"Following adapter(s) could not be found: {', '.join(missing)}. Make sure you are passing the correct adapter name(s)."
                    f" current loaded adapters are: {list(self.peft_config.keys())}"
                )
        elif adapter_name not in self.peft_config:
            raise ValueError(
                f"Adapter with name {adapter_name} not found. Please pass the correct adapter name among {list(self.peft_config.keys())}"
            )

        from peft.tuners.tuners_utils import BaseTunerLayer
        from peft.utils import ModulesToSaveWrapper

        _adapters_has_been_set = False

        for _, module in self.named_modules():
            if isinstance(module, (BaseTunerLayer, ModulesToSaveWrapper)):
                module.set_adapter(adapter_name)
                _adapters_has_been_set = True

        if not _adapters_has_been_set:
            raise ValueError(
                "Did not succeeded in setting the adapter. Please make sure you are using a model that supports adapters."
            )