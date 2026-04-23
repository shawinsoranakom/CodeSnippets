def _test_dequant_quant_lowering_helper(
        self,
        dtype,
        input_dtype=torch.float32,
        dequant_out_dtype=None,
    ):
        def fn(
            x,
            scale,
            zero_point,
            use_dequant,
            use_quant,
            quant_min,
            quant_max,
            dtype,
            dequant_out_dtype,
        ):
            if use_dequant:
                x = torch.ops.quantized_decomposed.dequantize_per_tensor(
                    x,
                    scale,
                    zero_point,
                    quant_min,
                    quant_max,
                    dtype,
                    out_dtype=dequant_out_dtype,
                )

            x = torch.relu(x)

            if use_quant:
                x = torch.ops.quantized_decomposed.quantize_per_tensor(
                    x, scale, zero_point, quant_min, quant_max, dtype
                )
            return x

        use_dequant_list = [False, True]
        use_quant_list = [False, True]
        use_tensor_overload_list = [False, True]

        if dtype not in [
            torch.uint8,
            torch.int8,
            torch.float8_e4m3fn,
            torch.float8_e5m2,
        ]:
            raise AssertionError(f"Unexpected dtype: {dtype}")
        quant_min = 0 if dtype == torch.uint8 else -128
        quant_max = 255 if dtype == torch.uint8 else 127
        if dtype in [torch.float8_e4m3fn, torch.float8_e5m2]:
            quant_min = int(torch.finfo(dtype).min)
            quant_max = int(torch.finfo(dtype).max)
            use_tensor_overload_list = [
                False,
            ]

        for (
            use_dequant,
            use_quant,
            use_tensor_overload,
        ) in itertools.product(
            use_dequant_list,
            use_quant_list,
            use_tensor_overload_list,
        ):
            x = torch.clamp(
                torch.randn((1, 7, 7, 9), dtype=input_dtype) * 100,
                quant_min,
                quant_max,
            )
            if use_dequant:
                x = x.to(dtype)
            zero_point = 100
            scale = 0.01
            if use_tensor_overload:
                zero_point = torch.tensor(zero_point, dtype=torch.int64)
                scale = torch.tensor(scale)
            with config.patch({"cpp.simdlen": None}):
                torch._dynamo.reset()
                metrics.reset()
                inputs = (
                    x,
                    scale,
                    zero_point,
                    use_dequant,
                    use_quant,
                    quant_min,
                    quant_max,
                    dtype,
                    dequant_out_dtype,
                )
                self.common(fn, inputs)
                check_metrics_vec_kernel_count(1)

                # Check that both main and tail loops are vectorized
                if dtype in [torch.float8_e4m3fn, torch.float8_e5m2]:
                    compiled_fn = torch.compile(fn)
                    _, code = run_and_get_cpp_code(compiled_fn, *inputs)
                    FileCheck().check_count("loadu", 2, exactly=True).run(code)