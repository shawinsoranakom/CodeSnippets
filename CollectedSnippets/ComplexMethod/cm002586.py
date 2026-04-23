def set_experts_implementation(self, experts_implementation: str | dict):
        """
        Set the requested `experts_implementation` for this model.

        Args:
            experts_implementation (`str` or `dict`):
                The experts implementation to set for this model. It can be either a `str`, in which case it will be
                dispatched to all submodels if relevant, or a `dict` where keys are the sub_configs name, in which case each
                submodel will dispatch the corresponding value.
        """
        requested_implementation = (
            experts_implementation
            if not isinstance(experts_implementation, dict)
            else experts_implementation.get("", self.config._experts_implementation)
        )

        if requested_implementation != self.config._experts_implementation:
            requested_implementation = self._check_and_adjust_experts_implementation(requested_implementation)
            # Apply the change (on the internal attr, to avoid setting it recursively)
            self.config._experts_implementation_internal = requested_implementation

        # Apply it to all submodels as well
        for submodule in self.modules():
            # We found a submodel (which is not self) with a different config (otherwise, it may be the same "actual model",
            # e.g. ForCausalLM has a Model inside, but no need to check it again)
            if (
                submodule is not self
                and isinstance(submodule, PreTrainedModel)
                and submodule.config.__class__ != self.config.__class__
            ):
                # Set the experts on the submodule
                sub_implementation = requested_implementation
                if isinstance(experts_implementation, dict):
                    for subconfig_key in self.config.sub_configs:
                        # We need to check for exact object match here, with `is`
                        if getattr(self.config, subconfig_key) is submodule.config:
                            sub_implementation = experts_implementation.get(
                                subconfig_key, submodule.config._experts_implementation
                            )
                            break
                # Check the module can use correctly, otherwise we raise an error if requested experts can't be set for submodule
                sub_implementation = submodule.get_correct_experts_implementation(sub_implementation)
                submodule.config._experts_implementation_internal = sub_implementation