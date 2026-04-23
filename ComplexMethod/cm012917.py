def _detect_per_channel_helper(self, model: nn.Module):
        r"""
        determines if per_channel quantization is supported in modules and submodules.

        Returns a dictionary in the higher level _detect_per_channel function.
        Each entry maps the fully-qualified-name to information on whether per_channel quantization.

        Args:
            model: The current module that is being checked to see if it is per_channel quantizable

        Returns dictionary mapping fqns to if per_channel quantization is possible
        """
        # create dict we will return
        per_channel_info: dict = {}

        # get the fully qualified name and check if in list of modules to include and list of modules to ignore
        for fqn, module in model.named_modules():
            is_in_include_list = any(
                isinstance(module, x) for x in self.supported_modules
            )

            # check if the module per_channel is supported
            # based on backend
            per_channel_supported = False

            if is_in_include_list:
                per_channel_supported = True

                # assert statement for MyPy
                q_config_file = module.qconfig
                if not isinstance(q_config_file, QConfig):
                    raise AssertionError("module.qconfig must be a QConfig")

                # this object should either be fake quant or observer
                q_or_s_obj = module.qconfig.weight.p.func()
                if not isinstance(q_or_s_obj, (FakeQuantize, ObserverBase)):
                    raise AssertionError(
                        "module.qconfig.weight must be a FakeQuantize or ObserverBase"
                    )

                per_channel_used = False  # will be true if found in qconfig

                if hasattr(
                    q_or_s_obj, "ch_axis"
                ):  # then we know that per_channel quantization used
                    # all fake quants have channel axis so need to check is_per_channel
                    if isinstance(q_or_s_obj, FakeQuantize):
                        if (
                            hasattr(q_or_s_obj, "is_per_channel")
                            and q_or_s_obj.is_per_channel
                        ):
                            per_channel_used = True
                    elif isinstance(q_or_s_obj, ObserverBase):
                        # should be an observer otherwise
                        per_channel_used = True
                    else:
                        raise ValueError("Should be either observer or fake quant")

                per_channel_info[fqn] = {
                    self.PER_CHAN_SUPPORTED_KEY: per_channel_supported,
                    self.PER_CHAN_USED_KEY: per_channel_used,
                    self.BACKEND_KEY: self.backend_chosen,
                }

        return per_channel_info