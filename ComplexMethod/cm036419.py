def check_model(model):
            # checks further down in the test case are hardcoded for this
            # model
            assert model_name == "ibm-granite/granite-3.0-1b-a400m-base"

            o_proj = model.model.layers[0].self_attn.o_proj
            moe = model.model.layers[0].block_sparse_moe.experts

            # o_proj and moe in layer 0 are always quantized (never ignored)
            # because of how we craft the test case inputs
            assert isinstance(o_proj.quant_method, expected_linear_cls)
            if moe is not None:
                assert isinstance(moe.quant_method, expected_moe_cls)

            if current_platform.is_cuda():
                assert o_proj.weight.dtype == torch.float8_e4m3fn
            elif current_platform.is_rocm():
                assert o_proj.weight.dtype == current_platform.fp8_dtype()
            else:
                pytest.skip("Only runs on CUDA and ROCm.")

            # Verify ignored layers are unquantized.
            if isinstance(online_quant_args, dict) and "ignore" in online_quant_args:
                # only .*1.self_attn_o_proj is skipped
                for layer_idx in range(len(model.model.layers)):
                    o_proj = model.model.layers[layer_idx].self_attn.o_proj
                    if layer_idx == 1:
                        assert isinstance(o_proj.quant_method, UnquantizedLinearMethod)
                    else:
                        assert isinstance(o_proj.quant_method, expected_linear_cls)

                # every .*self_attn.qkv_proj is skipped
                for layer_idx in range(len(model.model.layers)):
                    qkv_proj = model.model.layers[layer_idx].self_attn.qkv_proj
                    assert isinstance(qkv_proj.quant_method, UnquantizedLinearMethod)