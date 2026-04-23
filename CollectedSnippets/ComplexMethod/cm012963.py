def from_float(cls, mod, use_precomputed_fake_quant=False):
        if type(mod) not in {torch.nn.LSTM, torch.nn.GRU}:
            raise AssertionError(
                "nn.quantized.dynamic.RNNBase.from_float only works for nn.LSTM and nn.GRU"
            )
        if not hasattr(mod, "qconfig"):
            raise AssertionError("Input float module must have qconfig defined")

        if mod.qconfig is not None and mod.qconfig.weight is not None:
            weight_observer_method = mod.qconfig.weight
        else:
            # We have the circular import issues if we import the qconfig in the beginning of this file:
            # https://github.com/pytorch/pytorch/pull/24231. The current workaround is to postpone the
            # import until we need it.
            from torch.ao.quantization.qconfig import default_dynamic_qconfig

            weight_observer_method = default_dynamic_qconfig.weight

        dtype = weight_observer_method().dtype
        supported_scalar_types = [torch.qint8, torch.float16]
        if dtype not in supported_scalar_types:
            raise RuntimeError(
                f"Unsupported dtype for dynamic RNN quantization: {dtype}"
            )
        # RNNBase can be either LSTM or GRU
        qRNNBase: Union[LSTM, GRU]
        if mod.mode == "LSTM":
            qRNNBase = LSTM(
                mod.input_size,
                mod.hidden_size,
                mod.num_layers,
                mod.bias,
                mod.batch_first,
                mod.dropout,
                mod.bidirectional,
                dtype,
            )
        elif mod.mode == "GRU":
            qRNNBase = GRU(
                mod.input_size,
                mod.hidden_size,
                mod.num_layers,
                mod.bias,
                mod.batch_first,
                mod.dropout,
                mod.bidirectional,
                dtype,
            )
        else:
            raise NotImplementedError(
                "Only LSTM/GRU is supported for QuantizedRNN for now"
            )

        num_directions = 2 if mod.bidirectional else 1

        if not mod.bias:
            raise AssertionError("mod.bias must be True")

        _all_weight_values = []
        for layer in range(qRNNBase.num_layers):
            for direction in range(num_directions):
                suffix = "_reverse" if direction == 1 else ""

                def retrieve_weight_bias(ihhh):
                    weight_name = f"weight_{ihhh}_l{layer}{suffix}"
                    bias_name = f"bias_{ihhh}_l{layer}{suffix}"
                    weight = getattr(mod, weight_name)
                    bias = getattr(mod, bias_name)
                    return weight, bias

                weight_ih, bias_ih = retrieve_weight_bias("ih")
                weight_hh, bias_hh = retrieve_weight_bias("hh")

                if dtype == torch.qint8:

                    def quantize_and_pack(w, b):
                        weight_observer = weight_observer_method()
                        weight_observer(w)
                        qweight = _quantize_weight(w.float(), weight_observer)
                        packed_weight = torch.ops.quantized.linear_prepack(qweight, b)
                        return packed_weight

                    packed_ih = quantize_and_pack(weight_ih, bias_ih)
                    packed_hh = quantize_and_pack(weight_hh, bias_hh)
                    if qRNNBase.version is None or qRNNBase.version < 2:
                        cell_params = (
                            torch.ops.quantized.make_quantized_cell_params_dynamic(
                                packed_ih, packed_hh, bias_ih, bias_hh
                            )
                        )
                    else:
                        cell_params = (
                            torch.ops.quantized.make_quantized_cell_params_dynamic(
                                packed_ih, packed_hh, bias_ih, bias_hh, True
                            )
                        )

                elif dtype == torch.float16:
                    packed_ih = torch.ops.quantized.linear_prepack_fp16(
                        weight_ih.float(), bias_ih
                    )
                    packed_hh = torch.ops.quantized.linear_prepack_fp16(
                        weight_hh.float(), bias_hh
                    )

                    cell_params = torch.ops.quantized.make_quantized_cell_params_fp16(
                        packed_ih, packed_hh
                    )
                else:
                    raise RuntimeError(
                        "Unsupported dtype specified for dynamic quantized LSTM!"
                    )

                _all_weight_values.append(PackedParameter(cell_params))
        qRNNBase._all_weight_values = torch.nn.ModuleList(_all_weight_values)

        return qRNNBase