def check_model(model):
            layer = model.model.layers[0]

            qkv_proj = layer.self_attn.qkv_proj
            assert isinstance(qkv_proj.quant_method, CompressedTensorsLinearMethod)
            assert isinstance(qkv_proj.scheme, CompressedTensorsW8A8Fp8)
            assert isinstance(qkv_proj.scheme.fp8_linear, Fp8BlockScaledMMLinearKernel)

            assert qkv_proj.weight.dtype is fp8_dtype
            assert qkv_proj.weight_scale.dtype is torch.float32
            assert len(qkv_proj.weight.shape) == 2
            assert len(qkv_proj.weight_scale.shape) == 2

            input_quant_op = qkv_proj.scheme.fp8_linear.quant_fp8
            assert isinstance(input_quant_op, QuantFP8)
            assert input_quant_op._forward_method in (
                input_quant_op.forward_cuda,
                input_quant_op.forward_hip,
            )