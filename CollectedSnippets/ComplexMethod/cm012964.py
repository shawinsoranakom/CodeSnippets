def from_float(cls, mod, use_precomputed_fake_quant=False):
        if type(mod) not in {torch.nn.LSTMCell, torch.nn.GRUCell, torch.nn.RNNCell}:
            raise AssertionError(
                "nn.quantized.dynamic.RNNCellBase.from_float "
                "only works for nn.LSTMCell, nn.GRUCell and nn.RNNCell"
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

        qRNNCellBase: Union[LSTMCell, GRUCell, RNNCell]

        if type(mod) is torch.nn.LSTMCell:
            qRNNCellBase = LSTMCell(
                mod.input_size, mod.hidden_size, bias=mod.bias, dtype=dtype
            )
        elif type(mod) is torch.nn.GRUCell:
            qRNNCellBase = GRUCell(
                mod.input_size, mod.hidden_size, bias=mod.bias, dtype=dtype
            )
        elif type(mod) is torch.nn.RNNCell:
            qRNNCellBase = RNNCell(
                mod.input_size,
                mod.hidden_size,
                bias=mod.bias,
                nonlinearity=mod.nonlinearity,
                dtype=dtype,
            )
        else:
            raise NotImplementedError(
                "Only LSTMCell, GRUCell and RNNCell \
            are supported for QuantizedRNN for now"
            )

        if not mod.bias:
            raise AssertionError("mod.bias must be True")

        def _observe_and_quantize_weight(weight):
            if dtype == torch.qint8:
                weight_observer = weight_observer_method()
                weight_observer(weight)
                qweight = _quantize_weight(weight.float(), weight_observer)
                return qweight
            else:
                return weight.float()

        qRNNCellBase._packed_weight_ih = pack_weight_bias(
            _observe_and_quantize_weight(mod.weight_ih), mod.bias_ih, dtype
        )
        qRNNCellBase._packed_weight_hh = pack_weight_bias(
            _observe_and_quantize_weight(mod.weight_hh), mod.bias_hh, dtype
        )
        return qRNNCellBase