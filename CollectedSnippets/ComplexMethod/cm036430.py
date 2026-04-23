def check_model(model):
            layer = model.model.layers[0]

            qkv_proj = layer.self_attn.qkv_proj
            o_proj = layer.self_attn.o_proj
            gate_up_proj = layer.mlp.gate_up_proj
            down_proj = layer.mlp.down_proj

            for proj in (qkv_proj, o_proj, gate_up_proj, down_proj):
                assert isinstance(proj.quant_method, CompressedTensorsLinearMethod)
                assert isinstance(proj.scheme, scheme)

                assert proj.weight_packed.dtype is torch.int32
                assert proj.weight_scale.dtype is torch.float8_e4m3fn
                assert proj.weight_chan_scale.dtype is torch.float32
                assert proj.scheme.group_size == 128