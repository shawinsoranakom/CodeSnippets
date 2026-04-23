def check_model(model):
            layer = model.model.layers[0]

            qkv_proj = layer.self_attn.qkv_proj
            o_proj = layer.self_attn.o_proj
            gate_up_proj = layer.mlp.gate_up_proj
            down_proj = layer.mlp.down_proj

            from vllm.model_executor.layers.quantization.modelopt import (
                ModelOptFp8PcPtLinearMethod,
            )

            assert isinstance(qkv_proj.quant_method, ModelOptFp8PcPtLinearMethod)
            assert isinstance(o_proj.quant_method, ModelOptFp8PcPtLinearMethod)
            assert isinstance(gate_up_proj.quant_method, ModelOptFp8PcPtLinearMethod)
            assert isinstance(down_proj.quant_method, ModelOptFp8PcPtLinearMethod)

            assert qkv_proj.weight.dtype == torch.float8_e4m3fn
            assert o_proj.weight.dtype == torch.float8_e4m3fn
            assert gate_up_proj.weight.dtype == torch.float8_e4m3fn
            assert down_proj.weight.dtype == torch.float8_e4m3fn

            # Per-channel scales; activations are dynamically scaled per token.
            assert hasattr(qkv_proj, "weight_scale")
            assert qkv_proj.weight_scale.dtype == torch.float32
            assert qkv_proj.weight_scale.dim() == 1
            assert not hasattr(qkv_proj, "input_scale")

            assert hasattr(o_proj, "weight_scale")
            assert o_proj.weight_scale.dtype == torch.float32
            assert o_proj.weight_scale.dim() == 1
            assert not hasattr(o_proj, "input_scale")

            assert hasattr(gate_up_proj, "weight_scale")
            assert gate_up_proj.weight_scale.dtype == torch.float32
            assert gate_up_proj.weight_scale.dim() == 1
            assert not hasattr(gate_up_proj, "input_scale")

            assert hasattr(down_proj, "weight_scale")
            assert down_proj.weight_scale.dtype == torch.float32
            assert down_proj.weight_scale.dim() == 1
            assert not hasattr(down_proj, "input_scale")