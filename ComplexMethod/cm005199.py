def __post_init__(self, **kwargs):
        if (
            isinstance(self.intermediate_size, Sequence)
            and (intsize_len := len(self.intermediate_size)) != self.num_hidden_layers
        ):
            raise ValueError(
                "intermediate_size must have an explicit intermediate size for every layer or one for all layers. "
                f"Expected {self.num_hidden_layers} values but got {intsize_len}."
            )
        elif not isinstance(self.intermediate_size, Sequence):
            self.intermediate_size = [self.intermediate_size] * self.num_hidden_layers

        if self.layer_types is None:
            self.layer_types = [
                "full_attention" if (i + 1) % 5 == 0 else "sliding_attention" for i in range(self.num_hidden_layers)
            ]

        if self.activation_sparsity_pattern is None:
            num_sparse_layers = 10 if self.num_hidden_layers > 10 else 0
            self.activation_sparsity_pattern = [0.95] * num_sparse_layers + [0.0] * (
                self.num_hidden_layers - num_sparse_layers
            )

        if (len_asp := len(self.activation_sparsity_pattern)) != self.num_hidden_layers:
            raise ValueError(
                "activation_sparsity_pattern must have an explicit activation sparsity value for every layer."
                f"Expected {self.num_hidden_layers} values but got {len_asp}."
            )

        PreTrainedConfig.__post_init__(**kwargs)