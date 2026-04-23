def set_attn_implementation(self, attn_implementation: str | dict, allow_all_kernels: bool = False):
        """
        Set the requested `attn_implementation` for this model.

        Args:
            attn_implementation (`str` or `dict`):
                The attention implementation to set for this model. It can be either a `str`, in which case it will be
                dispatched to all submodels if relevant, or a `dict` where keys are the sub_configs name, in which case each
                submodel will dispatch the corresponding value.
            allow_all_kernels (`bool`, optional):
                Whether to load kernels from unverified hub repos, if `attn_implementation` is a custom kernel outside
                of the `kernels-community` hub repository.
        """
        requested_implementation = (
            attn_implementation
            if not isinstance(attn_implementation, dict)
            else attn_implementation.get("", self.config._attn_implementation)
        )

        if requested_implementation != self.config._attn_implementation:
            # In this case, raise
            if not self._can_set_attn_implementation():
                logger.warning(
                    f"{self.__class__.__name__} does not support setting its attention implementation dynamically, because it "
                    "does not follow the functional approach based on AttentionInterface "
                    "(see https://huggingface.co/docs/transformers/en/attention_interface)"
                )
            else:
                requested_implementation = self._check_and_adjust_attn_implementation(
                    requested_implementation, is_init_check=False, allow_all_kernels=allow_all_kernels
                )
                # Apply the change (on the internal attr, to avoid setting it recursively)
                self.config._attn_implementation_internal = requested_implementation

        # Apply it to all submodels as well
        for submodule in self.modules():
            # We found a submodel (which is not self) with a different config (otherwise, it may be the same "actual model",
            # e.g. ForCausalLM has a Model inside, but no need to check it again)
            if (
                submodule is not self
                and isinstance(submodule, PreTrainedModel)
                and submodule.config.__class__ != self.config.__class__
                # If it was already changed, no need to do it again
                and not hasattr(submodule.config, "_attn_was_changed")
            ):
                # In this case, warn and skip
                if not submodule._can_set_attn_implementation():
                    logger.warning(
                        f"{submodule.__class__.__name__} does not support setting its attention implementation dynamically, because it "
                        "does not follow the functional approach based on AttentionInterface "
                        "(see https://huggingface.co/docs/transformers/en/attention_interface)"
                    )
                # Set the attn on the submodule
                else:
                    sub_implementation = requested_implementation
                    if isinstance(attn_implementation, dict):
                        for subconfig_key in self.config.sub_configs:
                            # We need to check for exact object match here, with `is`
                            if getattr(self.config, subconfig_key) is submodule.config:
                                sub_implementation = attn_implementation.get(
                                    subconfig_key, submodule.config._attn_implementation
                                )
                                break
                    # Check the module can use correctly, otherwise we raise an error if requested attention can't be set for submodule
                    sub_implementation = submodule.get_correct_attn_implementation(sub_implementation)
                    submodule.config._attn_implementation_internal = sub_implementation

                # Still add it as "changed" even if it was skipped, as we would otherwise try to set it in the dark afterwards
                # We need to set it on the config itself, to differentiate 2 subconfigs of the same __class__ potentially
                submodule.config._attn_was_changed = True

        # We need this as some old and badly designed models use subconfigs without declaring the corresponding modules as PreTrainedModel
        for subconfig_key in self.config.sub_configs:
            if (subconfig := getattr(self.config, subconfig_key)) is not None:
                sub_implementation = (
                    requested_implementation
                    if not isinstance(attn_implementation, dict)
                    else attn_implementation.get(subconfig_key, subconfig._attn_implementation)
                )
                # This means we did not perform any check above for this particular subconfig -> set it in the dark if it is registered
                if (
                    not hasattr(subconfig, "_attn_was_changed")
                    # If it's already the same, then no need to enter here and raise warnings
                    and sub_implementation != subconfig._attn_implementation
                ):
                    if sub_implementation not in ["eager"] + ALL_ATTENTION_FUNCTIONS.valid_keys():
                        raise ValueError(
                            f'Specified `attn_implementation="{sub_implementation}"` is not supported for {subconfig_key}. '
                            'The only possible arguments are "eager" (manual attention implementation)'
                            f"or one of the following: {list(ALL_ATTENTION_FUNCTIONS.valid_keys())}"
                        )
                    subconfig._attn_implementation_internal = sub_implementation
                    logger.warning(
                        f"We set the attention implementation for the sub-config `{subconfig_key}` to `{sub_implementation}` "
                        "without finding the associated sub-model. For this reason we could not check if the model supports it. "
                        "You may encounter undefined behavior."
                    )
                # Unset the attribute in this case, to avoid issues in the future
                else:
                    if hasattr(subconfig, "_attn_was_changed"):
                        del subconfig._attn_was_changed