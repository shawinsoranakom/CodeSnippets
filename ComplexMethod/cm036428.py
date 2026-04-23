def check_model(model):
            layer = model.model.layers[0]

            qkv_proj = layer.self_attn.qkv_proj
            assert isinstance(qkv_proj.quant_method, CompressedTensorsLinearMethod)
            assert isinstance(qkv_proj.scheme, CompressedTensorsWNA16)

            assert qkv_proj.scheme.strategy == strategy
            assert qkv_proj.scheme.group_size == (-1 if group is None else group)

            assert qkv_proj.scheme.pack_factor == pack_factor
            assert qkv_proj.scheme.symmetric == symmetric
            assert qkv_proj.scheme.has_g_idx == has_g_idx