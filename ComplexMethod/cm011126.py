def _init_fqns(self) -> None:
        """Sets module and parameter FQN attributes for debugging."""
        if not self._is_root:
            raise AssertionError("Expected _is_root to be True")
        root_module = self._modules[0]
        param_to_fsdp_param: dict[nn.Parameter, FSDPParam] = {}
        # Build a mapping from module to all its FSDPParamGroups (not just one)
        module_to_fsdp_param_groups: dict[nn.Module, list[FSDPParamGroup]] = {}
        for state in self._state_ctx.all_states:
            for fsdp_param_group in state._fsdp_param_groups:
                for fsdp_param in fsdp_param_group.fsdp_params:
                    param_to_fsdp_param[fsdp_param.sharded_param] = fsdp_param
                for module in fsdp_param_group.modules:
                    if module not in module_to_fsdp_param_groups:
                        module_to_fsdp_param_groups[module] = []
                    module_to_fsdp_param_groups[module].append(fsdp_param_group)
        for param_name, param in root_module.named_parameters():
            if param in param_to_fsdp_param:
                param_to_fsdp_param[param]._param_fqn = param_name
        for module_name, module in root_module.named_modules():
            if module in module_to_fsdp_param_groups:
                # Set FQN for all param groups associated with this module
                for fsdp_param_group in module_to_fsdp_param_groups[module]:
                    module_fqn = fsdp_param_group._module_fqn
                    if module_fqn is None:
                        fsdp_param_group._module_fqn = module_name
                    else:
                        if not isinstance(module_fqn, str):
                            raise AssertionError(
                                f"Expected module_fqn to be str, got {type(module_fqn)}: {module_fqn}"
                            )
                        module_fqn += f", {module_name}"
                        fsdp_param_group._module_fqn = module_fqn