def __init__(
        self,
        mode,
        input_size,
        hidden_size,
        num_layers=1,
        bias=True,
        batch_first=False,
        dropout=0.0,
        bidirectional=False,
        dtype=torch.qint8,
    ):
        super().__init__()

        self.mode = mode
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.bias = bias
        self.batch_first = batch_first
        self.dropout = float(dropout)
        self.bidirectional = bidirectional
        self.dtype = dtype
        self.version = 2
        self.training = False
        num_directions = 2 if bidirectional else 1

        # "type: ignore" is required since ints and Numbers are not fully comparable
        # https://github.com/python/mypy/issues/8566
        if (
            not isinstance(dropout, numbers.Number)
            or not 0 <= dropout <= 1  # type: ignore[operator]
            or isinstance(dropout, bool)
        ):
            raise ValueError(
                "dropout should be a number in range [0, 1] "
                "representing the probability of an element being "
                "zeroed"
            )
        if dropout > 0 and num_layers == 1:  # type: ignore[operator]
            warnings.warn(
                "dropout option adds dropout after all but last "
                "recurrent layer, so non-zero dropout expects "
                f"num_layers greater than 1, but got dropout={dropout} and "
                f"num_layers={num_layers}",
                stacklevel=2,
            )

        if mode == "LSTM":
            gate_size = 4 * hidden_size
        elif mode == "GRU":
            gate_size = 3 * hidden_size
        else:
            raise ValueError("Unrecognized RNN mode: " + mode)

        _all_weight_values = []
        for layer in range(num_layers):
            for _ in range(num_directions):
                layer_input_size = (
                    input_size if layer == 0 else hidden_size * num_directions
                )

                w_ih = torch.randn(gate_size, layer_input_size).to(torch.float)
                w_hh = torch.randn(gate_size, hidden_size).to(torch.float)
                b_ih = torch.randn(gate_size).to(torch.float)
                b_hh = torch.randn(gate_size).to(torch.float)
                if dtype == torch.qint8:
                    w_ih = torch.quantize_per_tensor(
                        w_ih, scale=0.1, zero_point=0, dtype=torch.qint8
                    )
                    w_hh = torch.quantize_per_tensor(
                        w_hh, scale=0.1, zero_point=0, dtype=torch.qint8
                    )
                    packed_ih = torch.ops.quantized.linear_prepack(w_ih, b_ih)
                    packed_hh = torch.ops.quantized.linear_prepack(w_hh, b_hh)
                    # pyrefly: ignore [unnecessary-comparison]
                    if self.version is None or self.version < 2:
                        cell_params = (
                            torch.ops.quantized.make_quantized_cell_params_dynamic(
                                packed_ih, packed_hh, b_ih, b_hh
                            )
                        )
                    else:
                        cell_params = (
                            torch.ops.quantized.make_quantized_cell_params_dynamic(
                                packed_ih, packed_hh, b_ih, b_hh, True
                            )
                        )
                else:
                    packed_ih = torch.ops.quantized.linear_prepack_fp16(w_ih, b_ih)
                    packed_hh = torch.ops.quantized.linear_prepack_fp16(w_hh, b_hh)
                    cell_params = torch.ops.quantized.make_quantized_cell_params_fp16(
                        packed_ih, packed_hh
                    )

                _all_weight_values.append(PackedParameter(cell_params))
        self._all_weight_values = torch.nn.ModuleList(_all_weight_values)