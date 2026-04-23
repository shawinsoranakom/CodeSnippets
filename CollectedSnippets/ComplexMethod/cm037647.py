def process_weights_after_loading(self, layer) -> None:
        if self.strategy == QuantizationStrategy.TENSOR:
            weight, weight_scale, input_scale = process_fp8_weight_tensor_strategy(
                layer.weight,
                layer.weight_scale,
                layer.logical_widths,
                getattr(layer, "input_scale", None),
            )
            weight = weight.t()
        elif self.strategy == QuantizationStrategy.CHANNEL:
            weight, weight_scale, input_scale = process_fp8_weight_channel_strategy(
                layer.weight, layer.weight_scale, getattr(layer, "input_scale", None)
            )
            weight = weight.t()

        elif self.strategy == QuantizationStrategy.BLOCK:
            assert self.is_static_input_scheme is False
            self.fp8_linear.process_weights_after_loading(layer)

            layer.input_scale = None
            # fp8_linear.process_weights_after_loading applies the post process
            # and reassigns the weight and weight_scale buffers to layer attributes.
            return

        else:
            raise ValueError(
                f"Unknown quantization strategy {self.strategy}: "
                f"should be one of {list(QuantizationStrategy)}"
            )

        # required by torch.compile to be torch.nn.Parameter
        layer.weight = Parameter(weight.data, requires_grad=False)
        layer.weight_scale = Parameter(weight_scale.data, requires_grad=False)
        if input_scale is not None:
            layer.input_scale = Parameter(input_scale.data, requires_grad=False)

        # INPUT SCALE
        if self.is_static_input_scheme and hasattr(layer, "input_scale"):
            layer.input_scale = Parameter(layer.input_scale.max(), requires_grad=False)
        else:
            layer.input_scale = None

        if hasattr(self, "fp8_linear"):
            self.fp8_linear.process_weights_after_loading(layer)