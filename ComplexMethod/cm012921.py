def to_dict(self) -> dict[str, Any]:
        """
        Convert this ``BackendPatternConfig`` to a dictionary with the items described in
        :func:`~torch.ao.quantization.backend_config.BackendPatternConfig.from_dict`.
        """
        backend_pattern_config_dict: dict[str, Any] = {
            OBSERVATION_TYPE_DICT_KEY: self.observation_type,
            DTYPE_CONFIGS_DICT_KEY: [c.to_dict() for c in self.dtype_configs],
        }
        if self.pattern is not None:
            backend_pattern_config_dict[PATTERN_DICT_KEY] = self.pattern
        if self.root_module is not None:
            backend_pattern_config_dict[ROOT_MODULE_DICT_KEY] = self.root_module
        if self.qat_module is not None:
            backend_pattern_config_dict[QAT_MODULE_DICT_KEY] = self.qat_module
        if self.reference_quantized_module is not None:
            backend_pattern_config_dict[REFERENCE_QUANTIZED_MODULE_DICT_KEY] = (
                self.reference_quantized_module
            )
        if self.fused_module is not None:
            backend_pattern_config_dict[FUSED_MODULE_DICT_KEY] = self.fused_module
        if self.fuser_method is not None:
            backend_pattern_config_dict[FUSER_METHOD_DICT_KEY] = self.fuser_method
        if self._root_node_getter is not None:
            backend_pattern_config_dict[ROOT_NODE_GETTER_DICT_KEY] = (
                self._root_node_getter
            )
        if self._extra_inputs_getter is not None:
            backend_pattern_config_dict[EXTRA_INPUTS_GETTER_DICT_KEY] = (
                self._extra_inputs_getter
            )
        if len(self._num_tensor_args_to_observation_type) > 0:
            backend_pattern_config_dict[
                NUM_TENSOR_ARGS_TO_OBSERVATION_TYPE_DICT_KEY
            ] = self._num_tensor_args_to_observation_type
        if len(self._input_type_to_index) > 0:
            backend_pattern_config_dict[INPUT_TYPE_TO_INDEX_DICT_KEY] = (
                self._input_type_to_index
            )
        if self._pattern_complex_format is not None:
            backend_pattern_config_dict[PATTERN_COMPLEX_FORMAT_DICT_KEY] = (
                self._pattern_complex_format
            )
        return backend_pattern_config_dict