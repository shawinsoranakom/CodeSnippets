def _test_common(
        self,
        mod,
        inputs,
        matcher_check_fn,
        atol=1e-5,
        rtol=1.3e-6,
        check_autocast=torch.float32,
        check_quantization=False,
        is_qat=False,
        dtype=None,
        is_dynamic=False,
        quantizer=None,
        compile_options={},  # noqa: B006
        quantization_with_autocast=False,
    ):
        if not hasattr(self, "device"):
            has_xpu = any(
                isinstance(input, torch.Tensor) and input.device.type == "xpu"
                for input in inputs
            )
            device = "xpu" if has_xpu else "cpu"
        else:
            device = self.device

        mod = mod.to(device=device)
        if device != "cpu":
            inputs = tuple(
                clone_preserve_strides_offset(x, device=device) for x in inputs
            )
        counters.clear()
        torch._dynamo.reset()
        if check_autocast == torch.bfloat16 and is_mkldnn_bf16_supported(device):
            maybe_autocast = torch.amp.autocast(
                device_type=device, dtype=torch.bfloat16
            )
            atol, rtol = 5e-2, 5e-2
        elif check_autocast == torch.float16 and (is_mkldnn_fp16_supported(device)):
            maybe_autocast = torch.amp.autocast(device_type=device, dtype=torch.float16)
            atol, rtol = 5e-2, 5e-2
        else:
            if check_autocast != torch.float32:
                raise AssertionError(
                    f"Expected check_autocast to be torch.float32, got {check_autocast}"
                )
            maybe_autocast = contextlib.nullcontext()
        if check_quantization:
            raise NotImplementedError("not supported, please migrate to torchao")
            """
            if quantization_with_autocast:
                with maybe_autocast:
                    convert_model = _generate_qdq_quantized_model(
                        mod, inputs, is_qat, is_dynamic, quantizer
                    )
            else:
                convert_model = _generate_qdq_quantized_model(
                    mod, inputs, is_qat, is_dynamic, quantizer
                )
            with torch.no_grad(), maybe_autocast:
                _ = torch.compile(convert_model)(*inputs)
                matcher_check_fn()
            """
        else:
            with torch.no_grad(), maybe_autocast:
                clone_inputs = self._clone_inputs(inputs)
                expected = mod(*inputs)
                actual = torch.compile(mod, **compile_options)(*clone_inputs)
                if self.precision != 0:
                    torch.testing.assert_close(
                        actual, expected, atol=self.precision, rtol=self.precision
                    )
                else:
                    torch.testing.assert_close(actual, expected, atol=atol, rtol=rtol)
                matcher_check_fn()