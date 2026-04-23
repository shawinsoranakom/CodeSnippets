def __init__(
        self,
        input_dim,
        output_dim,
        embeddings_initializer="uniform",
        embeddings_regularizer=None,
        embeddings_constraint=None,
        mask_zero=False,
        weights=None,
        lora_rank=None,
        lora_alpha=None,
        quantization_config=None,
        **kwargs,
    ):
        if (
            not isinstance(input_dim, int)
            or isinstance(input_dim, bool)
            or input_dim <= 0
        ):
            raise ValueError(
                "`input_dim` must be a positive integer. "
                f"Received: input_dim={input_dim} "
                f"(of type {type(input_dim).__name__})."
            )
        if (
            not isinstance(output_dim, int)
            or isinstance(output_dim, bool)
            or output_dim <= 0
        ):
            raise ValueError(
                "`output_dim` must be a positive integer. "
                f"Received: output_dim={output_dim} "
                f"(of type {type(output_dim).__name__})."
            )
        input_length = kwargs.pop("input_length", None)
        if input_length is not None:
            warnings.warn(
                "Argument `input_length` is deprecated. Just remove it."
            )
        super().__init__(**kwargs)
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.embeddings_initializer = initializers.get(embeddings_initializer)
        self.embeddings_regularizer = regularizers.get(embeddings_regularizer)
        self.embeddings_constraint = constraints.get(embeddings_constraint)
        self.mask_zero = mask_zero
        self.supports_masking = mask_zero
        self.autocast = False
        self.lora_rank = lora_rank
        self.lora_alpha = lora_alpha if lora_alpha is not None else lora_rank
        self.lora_enabled = False
        self.quantization_config = quantization_config

        if weights is not None:
            self.build()
            if not (isinstance(weights, list) and len(weights) == 1):
                weights = [weights]
            self.set_weights(weights)