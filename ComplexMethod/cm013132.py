def checkObservers(
        self, module, propagate_qconfig_list=None, prepare_custom_config_dict=None
    ):
        r"""Checks the module or module's leaf descendants
        have observers in preparation for quantization
        """
        if propagate_qconfig_list is None:
            propagate_qconfig_list = get_default_qconfig_propagation_list()
        if prepare_custom_config_dict is None:
            prepare_custom_config_dict = {}
        float_to_observed_module_class_mapping = prepare_custom_config_dict.get(
            "float_to_observed_custom_module_class", {}
        )

        # check if a module is a leaf module, ignoring activation_post_process attribute
        def is_leaf_module(module):
            submodule_name_count = 0
            for name, _ in module.named_children():
                if name != "activation_post_process":
                    submodule_name_count += 1
            return submodule_name_count == 0

        if (
            hasattr(module, "qconfig")
            and module.qconfig is not None
            and (
                (
                    is_leaf_module(module)
                    and not isinstance(module, torch.nn.Sequential)
                    and type(module) in propagate_qconfig_list
                )
                or type(module) in float_to_observed_module_class_mapping
            )
            and not isinstance(module, torch.ao.quantization.DeQuantStub)
        ):
            self.assertTrue(
                hasattr(module, "activation_post_process"),
                "module: " + str(type(module)) + " do not have observer",
            )
        # we don't need to check observers for child modules of the
        # qat modules
        if (
            type(module) not in get_default_qat_module_mappings().values()
            and type(module) not in float_to_observed_module_class_mapping.values()
            and not isinstance(module, _FusedModule)
        ):
            for child in module.children():
                if type(child) is nn.Dropout:
                    continue
                self.checkObservers(
                    child, propagate_qconfig_list, prepare_custom_config_dict
                )