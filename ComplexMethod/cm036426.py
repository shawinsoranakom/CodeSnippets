def check_model(model):
            fc1 = model.model.decoder.layers[0].fc1
            assert isinstance(fc1.quant_method, Fp8LinearMethod)
            if kv_cache_dtype == "fp8":
                attn = model.model.decoder.layers[0].self_attn.attn
                assert isinstance(attn.quant_method, Fp8KVCacheMethod)
                assert attn._k_scale == 1.0
                assert attn._v_scale == 1.0

            if current_platform.is_cuda():
                if current_platform.supports_fp8() and not force_marlin:
                    # For GPUs with hardware support, we keep weights in fp8
                    assert fc1.weight.dtype == torch.float8_e4m3fn
                else:
                    # For GPUs without hardware support, we pack the fp8 weights
                    # for weight-only quantization using Marlin kernels
                    assert fc1.weight.dtype == torch.int32
            elif current_platform.is_rocm():
                if current_platform.supports_fp8() and not force_marlin:
                    # For GPUs with hardware support, we keep weights in fp8
                    assert fc1.weight.dtype == current_platform.fp8_dtype()
                else:  # unsupported ROCm platform
                    pytest.skip(
                        "Skip `test_load_fp16_model`. "
                        "It only runs on ROCm platform with FP8 compute."
                        " e.g. MI300X and above."
                    )
            else:  # unsupported platform
                pytest.skip(
                    "Skip `test_load_fp16_model`. "
                    "It only runs on CUDA and ROCm platform."
                )