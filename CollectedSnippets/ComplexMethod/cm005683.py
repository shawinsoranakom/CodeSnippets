def __init__(
        self,
        load_in_8bit=False,
        load_in_4bit=False,
        llm_int8_threshold=6.0,
        llm_int8_skip_modules=None,
        llm_int8_enable_fp32_cpu_offload=False,
        llm_int8_has_fp16_weight=False,
        bnb_4bit_compute_dtype=None,
        bnb_4bit_quant_type="fp4",
        bnb_4bit_use_double_quant=False,
        bnb_4bit_quant_storage=None,
        **kwargs,
    ):
        self.quant_method = QuantizationMethod.BITS_AND_BYTES

        if load_in_4bit and load_in_8bit:
            raise ValueError("load_in_4bit and load_in_8bit are both True, but only one can be used at the same time")

        self._load_in_8bit = load_in_8bit
        self._load_in_4bit = load_in_4bit
        self.llm_int8_threshold = llm_int8_threshold
        self.llm_int8_skip_modules = llm_int8_skip_modules
        self.llm_int8_enable_fp32_cpu_offload = llm_int8_enable_fp32_cpu_offload
        self.llm_int8_has_fp16_weight = llm_int8_has_fp16_weight
        self.bnb_4bit_quant_type = bnb_4bit_quant_type
        self.bnb_4bit_use_double_quant = bnb_4bit_use_double_quant

        if bnb_4bit_compute_dtype is None:
            self.bnb_4bit_compute_dtype = torch.float32
        elif isinstance(bnb_4bit_compute_dtype, str):
            self.bnb_4bit_compute_dtype = getattr(torch, bnb_4bit_compute_dtype)
        elif isinstance(bnb_4bit_compute_dtype, torch.dtype):
            self.bnb_4bit_compute_dtype = bnb_4bit_compute_dtype
        else:
            raise ValueError("bnb_4bit_compute_dtype must be a string or a torch.dtype")

        if bnb_4bit_quant_storage is None:
            self.bnb_4bit_quant_storage = torch.uint8
        elif isinstance(bnb_4bit_quant_storage, str):
            if bnb_4bit_quant_storage not in ["float16", "float32", "int8", "uint8", "float64", "bfloat16"]:
                raise ValueError(
                    "`bnb_4bit_quant_storage` must be a valid string (one of 'float16', 'float32', 'int8', 'uint8', 'float64', 'bfloat16') "
                )
            self.bnb_4bit_quant_storage = getattr(torch, bnb_4bit_quant_storage)
        elif isinstance(bnb_4bit_quant_storage, torch.dtype):
            self.bnb_4bit_quant_storage = bnb_4bit_quant_storage
        else:
            raise ValueError("bnb_4bit_quant_storage must be a string or a torch.dtype")

        if kwargs:
            logger.info(f"Unused kwargs: {list(kwargs.keys())}. These kwargs are not used in {self.__class__}.")

        self.post_init()