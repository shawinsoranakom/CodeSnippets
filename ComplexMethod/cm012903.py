def to_dict(self) -> dict[str, Any]:
        """
        Convert this ``PrepareCustomConfig`` to a dictionary with the items described in
        :func:`~torch.ao.quantization.fx.custom_config.PrepareCustomConfig.from_dict`.
        """

        def _make_tuple(key: Any, e: StandaloneModuleConfigEntry):
            qconfig_dict = e.qconfig_mapping.to_dict() if e.qconfig_mapping else None
            prepare_custom_config_dict = (
                e.prepare_custom_config.to_dict() if e.prepare_custom_config else None
            )
            return (
                key,
                qconfig_dict,
                e.example_inputs,
                prepare_custom_config_dict,
                e.backend_config,
            )

        d: dict[str, Any] = {}
        for module_name, sm_config_entry in self.standalone_module_names.items():
            if STANDALONE_MODULE_NAME_DICT_KEY not in d:
                d[STANDALONE_MODULE_NAME_DICT_KEY] = []
            d[STANDALONE_MODULE_NAME_DICT_KEY].append(
                _make_tuple(module_name, sm_config_entry)
            )
        for module_class, sm_config_entry in self.standalone_module_classes.items():
            if STANDALONE_MODULE_CLASS_DICT_KEY not in d:
                d[STANDALONE_MODULE_CLASS_DICT_KEY] = []
            d[STANDALONE_MODULE_CLASS_DICT_KEY].append(
                _make_tuple(module_class, sm_config_entry)
            )
        for (
            quant_type,
            float_to_observed_mapping,
        ) in self.float_to_observed_mapping.items():
            if FLOAT_TO_OBSERVED_DICT_KEY not in d:
                d[FLOAT_TO_OBSERVED_DICT_KEY] = {}
            d[FLOAT_TO_OBSERVED_DICT_KEY][_get_quant_type_to_str(quant_type)] = (
                float_to_observed_mapping
            )
        if len(self.non_traceable_module_names) > 0:
            d[NON_TRACEABLE_MODULE_NAME_DICT_KEY] = self.non_traceable_module_names
        if len(self.non_traceable_module_classes) > 0:
            d[NON_TRACEABLE_MODULE_CLASS_DICT_KEY] = self.non_traceable_module_classes
        if len(self.input_quantized_indexes) > 0:
            d[INPUT_QUANTIZED_INDEXES_DICT_KEY] = self.input_quantized_indexes
        if len(self.output_quantized_indexes) > 0:
            d[OUTPUT_QUANTIZED_INDEXES_DICT_KEY] = self.output_quantized_indexes
        if len(self.preserved_attributes) > 0:
            d[PRESERVED_ATTRIBUTES_DICT_KEY] = self.preserved_attributes
        return d