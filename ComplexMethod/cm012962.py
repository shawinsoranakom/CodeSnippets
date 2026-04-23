def set_weight_bias(self, weight_bias_dict):
        def weight_bias_name(ihhh, layer, suffix):
            weight_name = f"weight_{ihhh}_l{layer}{suffix}"
            bias_name = f"bias_{ihhh}_l{layer}{suffix}"
            return weight_name, bias_name

        num_directions = 2 if self.bidirectional else 1
        # TODO: dedup with __init__ of RNNBase
        _all_weight_values = []
        for layer in range(self.num_layers):
            for direction in range(num_directions):
                suffix = "_reverse" if direction == 1 else ""
                w_ih_name, b_ih_name = weight_bias_name("ih", layer, suffix)
                w_hh_name, b_hh_name = weight_bias_name("hh", layer, suffix)
                w_ih = weight_bias_dict[w_ih_name]
                b_ih = weight_bias_dict[b_ih_name]
                w_hh = weight_bias_dict[w_hh_name]
                b_hh = weight_bias_dict[b_hh_name]
                if w_ih.dtype == torch.qint8:
                    packed_ih = torch.ops.quantized.linear_prepack(w_ih, b_ih)
                    packed_hh = torch.ops.quantized.linear_prepack(w_hh, b_hh)
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