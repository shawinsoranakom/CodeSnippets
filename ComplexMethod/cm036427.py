def check_model(model):
            layer = model.model.layers[0]

            qkv_proj = layer.self_attn.qkv_proj
            o_proj = layer.self_attn.o_proj
            gate_up_proj = layer.mlp.gate_up_proj
            down_proj = layer.mlp.down_proj

            # assert zp for symmetric and asymmetric cases
            def zp_valid(zp: torch.Tensor | None):
                if is_symmetric:
                    return zp is None

                return zp is not None and zp.dtype is torch.int32

            assert zp_valid(qkv_proj.input_zero_point)
            assert zp_valid(o_proj.input_zero_point)
            assert zp_valid(gate_up_proj.input_zero_point)
            assert zp_valid(down_proj.input_zero_point)

            assert isinstance(qkv_proj.quant_method, CompressedTensorsLinearMethod)
            assert isinstance(o_proj.quant_method, CompressedTensorsLinearMethod)
            assert isinstance(gate_up_proj.quant_method, CompressedTensorsLinearMethod)
            assert isinstance(down_proj.quant_method, CompressedTensorsLinearMethod)
            assert isinstance(qkv_proj.scheme, CompressedTensorsW8A8Int8)

            assert qkv_proj.scheme.strategy == strategy
            assert qkv_proj.scheme.is_static_input_scheme
            expected_type = torch.int8

            assert qkv_proj.weight.dtype is expected_type
            assert o_proj.weight.dtype is expected_type
            assert gate_up_proj.weight.dtype is expected_type

            if qkv_proj.scheme.strategy == "tensor":
                # Make sure it is a channelwise buffer
                # After running process_weights_after_loading
                assert len(qkv_proj.weight_scale.shape) == 2
                assert qkv_proj.weight_scale.shape[0] == shape_0
                assert qkv_proj.weight_scale.shape[1] == 1
            assert qkv_proj.weight_scale.dtype is torch.float32
            assert qkv_proj.input_scale.dtype is torch.float32