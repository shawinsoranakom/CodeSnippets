def __init__(
        self,
        dataset,
        tokenizer,
        *,
        weight_bits: int = 4,
        num_samples: int = 128,
        per_channel: bool = True,
        sequence_length: int = 512,
        hessian_damping: float = 0.01,
        group_size: int = 128,
        symmetric: bool = False,
        activation_order: bool = False,
        quantization_layer_structure: dict = None,
    ):
        super().__init__()
        if weight_bits not in [2, 3, 4, 8]:
            raise ValueError(
                f"Unsupported weight_bits {weight_bits}. "
                "Supported values are 2, 3, 4, and 8."
            )
        if num_samples <= 0:
            raise ValueError("num_samples must be a positive integer.")
        if sequence_length <= 0:
            raise ValueError("sequence_length must be a positive integer.")
        if hessian_damping < 0 or hessian_damping > 1:
            raise ValueError("hessian_damping must be between 0 and 1.")
        if group_size < -1 or group_size == 0:
            raise ValueError(
                "Invalid group_size. Supported values are -1 (whole-tensor) "
                "or a positive integer, "
                f"but got {group_size}."
            )
        self.dataset = dataset
        self.tokenizer = tokenizer
        self.num_samples = num_samples
        self.per_channel = per_channel
        self.sequence_length = sequence_length
        self.hessian_damping = hessian_damping
        self.weight_bits = weight_bits
        self.group_size = group_size
        self.symmetric = symmetric
        self.activation_order = activation_order
        self.quantization_layer_structure = quantization_layer_structure