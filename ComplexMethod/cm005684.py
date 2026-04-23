def post_init(self):
        r"""
        Safety checker that arguments are correct - also replaces some NoneType arguments with their default values.
        """
        if not isinstance(self.load_in_4bit, bool):
            raise TypeError("load_in_4bit must be a boolean")

        if not isinstance(self.load_in_8bit, bool):
            raise TypeError("load_in_8bit must be a boolean")

        if not isinstance(self.llm_int8_threshold, float):
            raise TypeError("llm_int8_threshold must be a float")

        if self.llm_int8_skip_modules is not None and not isinstance(self.llm_int8_skip_modules, list):
            raise TypeError("llm_int8_skip_modules must be a list of strings")
        if not isinstance(self.llm_int8_enable_fp32_cpu_offload, bool):
            raise TypeError("llm_int8_enable_fp32_cpu_offload must be a boolean")

        if not isinstance(self.llm_int8_has_fp16_weight, bool):
            raise TypeError("llm_int8_has_fp16_weight must be a boolean")

        if self.bnb_4bit_compute_dtype is not None and not isinstance(self.bnb_4bit_compute_dtype, torch.dtype):
            raise TypeError("bnb_4bit_compute_dtype must be torch.dtype")

        if not isinstance(self.bnb_4bit_quant_type, str):
            raise TypeError("bnb_4bit_quant_type must be a string")

        if not isinstance(self.bnb_4bit_use_double_quant, bool):
            raise TypeError("bnb_4bit_use_double_quant must be a boolean")