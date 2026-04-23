def check_model(model):
            layer = model.model.layers[0]

            qkv_proj = layer.self_attn.qkv_proj
            o_proj = layer.self_attn.o_proj
            gate_up_proj = layer.mlp.gate_up_proj
            down_proj = layer.mlp.down_proj

            # Check that ModelOpt quantization method is properly applied
            from vllm.model_executor.layers.quantization.modelopt import (
                ModelOptFp8LinearMethod,
            )

            assert isinstance(qkv_proj.quant_method, ModelOptFp8LinearMethod)
            assert isinstance(o_proj.quant_method, ModelOptFp8LinearMethod)
            assert isinstance(gate_up_proj.quant_method, ModelOptFp8LinearMethod)
            assert isinstance(down_proj.quant_method, ModelOptFp8LinearMethod)

            # Check weight dtype is FP8
            assert qkv_proj.weight.dtype == torch.float8_e4m3fn
            assert o_proj.weight.dtype == torch.float8_e4m3fn
            assert gate_up_proj.weight.dtype == torch.float8_e4m3fn
            assert down_proj.weight.dtype == torch.float8_e4m3fn

            # Check scales are present and have correct dtype
            assert hasattr(qkv_proj, "weight_scale")
            assert hasattr(qkv_proj, "input_scale")
            assert qkv_proj.weight_scale.dtype == torch.float32
            assert qkv_proj.input_scale.dtype == torch.float32

            assert hasattr(o_proj, "weight_scale")
            assert hasattr(o_proj, "input_scale")
            assert o_proj.weight_scale.dtype == torch.float32
            assert o_proj.input_scale.dtype == torch.float32

            assert hasattr(gate_up_proj, "weight_scale")
            assert hasattr(gate_up_proj, "input_scale")
            assert gate_up_proj.weight_scale.dtype == torch.float32
            assert gate_up_proj.input_scale.dtype == torch.float32

            assert hasattr(down_proj, "weight_scale")
            assert hasattr(down_proj, "input_scale")
            assert down_proj.weight_scale.dtype == torch.float32
            assert down_proj.input_scale.dtype == torch.float32