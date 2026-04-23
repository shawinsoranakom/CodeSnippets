def _test_encoder_eager_matches_sdpa_inference(
    self,
    dtype,
    output_attentions,
    enable_kernels,
    atols=None,
    rtols=None,
):
    """
    This test is written as a regular function to be able to overload it easily with different tolerances.
    Otherwise, `parameterize.expand` prevents it as it removes the original function from the namespace.
    """
    if not self.has_attentions:
        self.skipTest(reason="Model architecture does not support attentions")

    if not self.all_model_classes[0]._supports_sdpa:
        self.skipTest(f"{self.all_model_classes[0].__name__} does not support SDPA")

    # convert shorthand name to torch.dtype
    if dtype == "fp16":
        dtype = torch.float16
    elif dtype == "bf16":
        dtype = torch.bfloat16
    elif dtype == "fp32":
        dtype = torch.float32

    if not is_torch_fp16_available_on_device(torch_device) and dtype == torch.float16:
        self.skipTest(f"float16 not supported on {torch_device} (on the specific device currently used)")

    if not is_torch_bf16_available_on_device(torch_device) and dtype == torch.bfloat16:
        self.skipTest(
            f"bfloat16 not supported on {torch_device} (on the specific device currently used, e.g. Nvidia T4 GPU)"
        )

    # Dictionary of tolerances for eager <> sdpa tests. Key = (device, sdpa_kernels_enabled, dtype)
    if atols is None:
        atols = {
            ("cpu", False, torch.float32): 1e-6,
            ("cpu", False, torch.float16): 5e-3,
            ("cpu", False, torch.bfloat16): 1e-2,
            ("cpu", True, torch.float32): 1e-6,
            ("cpu", True, torch.float16): 5e-3,
            ("cpu", True, torch.bfloat16): 1e-2,
            ("cuda", False, torch.float32): 1e-6,
            ("cuda", False, torch.bfloat16): 1e-2,
            ("cuda", False, torch.float16): 5e-3,
            ("cuda", True, torch.float32): 1e-6,
            ("cuda", True, torch.bfloat16): 1e-2,
            ("cuda", True, torch.float16): 5e-3,
        }
    if rtols is None:
        rtols = {
            ("cpu", False, torch.float32): 1e-4,
            ("cpu", False, torch.float16): 5e-3,
            ("cpu", False, torch.bfloat16): 1e-2,
            ("cpu", True, torch.float32): 1e-4,
            ("cpu", True, torch.float16): 5e-3,
            ("cpu", True, torch.bfloat16): 1e-2,
            ("cuda", False, torch.float32): 1e-4,
            ("cuda", False, torch.bfloat16): 1e-2,
            ("cuda", False, torch.float16): 5e-3,
            ("cuda", True, torch.float32): 1e-4,
            ("cuda", True, torch.bfloat16): 3e-2,  # (different from others)
            ("cuda", True, torch.float16): 5e-3,
        }

    for model_class in self.all_model_classes:
        config, inputs_dict = self.model_tester.prepare_config_and_inputs_for_common()
        set_config_for_less_flaky_test(config)

        model = model_class(config)

        with tempfile.TemporaryDirectory() as tmpdirname:
            model.save_pretrained(tmpdirname)
            model_from_pretrained_kwargs = {
                "pretrained_model_name_or_path": tmpdirname,
                "dtype": dtype,
            }

            if hasattr(config, "use_mask_token") or "use_mask_token" in inspect.signature(model.__init__).parameters:
                model_from_pretrained_kwargs["use_mask_token"] = True

            # TODO: remove this try/except, models should have a shared API
            try:
                model_sdpa = model_class.from_pretrained(**model_from_pretrained_kwargs, attn_implementation="sdpa")
            except ValueError:
                model_sdpa = model_class.from_pretrained(**model_from_pretrained_kwargs)
            model_sdpa = model_sdpa.eval().to(torch_device)

            model_eager = model_class.from_pretrained(**model_from_pretrained_kwargs, attn_implementation="eager")
            model_eager = model_eager.eval().to(torch_device)

        set_model_for_less_flaky_test(model_eager)
        set_model_for_less_flaky_test(model_sdpa)

        # TODO: if we can also check with `batch_size=1` without being flaky?
        for batch_size in [7]:
            input_data_batch_size = batch_size

            processed_inputs = {}
            processed_inputs[model.main_input_name] = inputs_dict[model.main_input_name]

            for key in getattr(self, "additional_model_inputs", []):
                # Some models don't have all `additional_model_inputs`, especially when we
                # craft cases to test model in different settings
                if key in inputs_dict:
                    processed_inputs[key] = inputs_dict[key]

            for key, value in processed_inputs.items():
                if torch.is_floating_point(value):
                    value = value.to(dtype)

                if key == "pixel_values":
                    continue

                # extend value to have at least `input_data_batch_size` elements
                if value.shape[0] < input_data_batch_size:
                    size = (input_data_batch_size - value.shape[0], *value.shape[1:])
                    if key == "grid_thw":
                        extension = torch.randint(high=5, size=size, dtype=value.dtype, device=torch_device)
                    elif key == "merge_sizes":
                        extension = torch.ones(size=size, dtype=value.dtype, device=torch_device)
                    value = torch.cat((value, extension), dim=0).to(torch_device)

                processed_inputs[key] = value[:input_data_batch_size]

            pixel_values = processed_inputs["pixel_values"]
            target_len = torch.sum(processed_inputs["grid_thw"].prod(dim=1) // (processed_inputs["merge_sizes"] ** 2))
            if pixel_values.size(0) < target_len:
                size = (input_data_batch_size - value.shape[0], *value.shape[1:])
                extension = torch.randn(
                    size=(target_len - pixel_values.size(0)), dtype=pixel_values.dtype, device=torch_device
                )
            elif pixel_values.size(0) > target_len:
                pixel_values = pixel_values[:target_len]
            processed_inputs["pixel_values"] = pixel_values

            processed_inputs.update(
                {
                    "output_hidden_states": True,
                    "output_attentions": output_attentions,
                }
            )

            # TODO: test gradients as well (& for FA2 as well!)
            with torch.no_grad():
                with sdpa_kernel(
                    enable_flash=enable_kernels,
                    enable_math=True,
                    enable_mem_efficient=enable_kernels,
                ):
                    prepared_inputs = self._prepare_for_class(processed_inputs, model_class)
                    prepared_inputs = {
                        k: v.to(torch_device) if isinstance(v, torch.Tensor) else v for k, v in prepared_inputs.items()
                    }
                    outputs_eager = model_eager(**prepared_inputs)
                    outputs_sdpa = model_sdpa(**prepared_inputs)

            key = "hidden_states"

            # TODO: rename logits -> hidden_states
            logits_eager = outputs_eager[key][-1]
            logits_sdpa = outputs_sdpa[key][-1]

            if torch_device in ["cpu", "cuda"]:
                atol = atols[torch_device, enable_kernels, dtype]
                rtol = rtols[torch_device, enable_kernels, dtype]
            elif torch_device == "hpu":
                atol = atols["cuda", enable_kernels, dtype]
                rtol = rtols["cuda", enable_kernels, dtype]
            elif torch_device == "xpu":
                # As of PyTorch 2.5 XPU backend supports only torch.nn.attention.SDPBackend.MATH
                # which is implemented on PyTorch level using aten operators and is
                # device agnostic with respect to implementation of each aten operator.
                atol = atols["cuda", False, dtype]
                rtol = rtols["cuda", False, dtype]
            else:
                atol = 1e-7
                rtol = 1e-4

            # Avoid test flakiness with bf16!
            # bf16 is not good at precision when the magnitude is larger. We have some models like `SiglipVision` with
            # this test passing all the time for fp32/fp16 but flaky with bf16. Furthermore, `llama` and `clip` have
            # this test passing all the time for bf16: it turns out their outputs are of smaller size (0.1 and 1.0)
            # while `siglip` has outputs with maximal values around 3.0/4.0.
            outputs_magnitude = float(
                (torch.max(logits_sdpa.abs().amax(), logits_eager.abs().amax())).detach().to("cpu")
            )
            # The choice of `3e-2` in `outputs_magnitude * 1e-2` might not work if a model has even more larger outputs.
            # (we can try to analyze the `rtol` more closely element-wise in the future and adjust the `rtol` instead of `atol`).
            computed_atol = outputs_magnitude * 3e-2
            if dtype == torch.bfloat16:
                atol = max(atol, computed_atol)

            results = [
                torch.allclose(_logits_sdpa, _logits_eager, atol=atol, rtol=rtol)
                for (_logits_sdpa, _logits_eager) in zip(logits_sdpa, logits_eager)
            ]

            # If 80% batch elements have matched results, it's fine
            if np.mean(results) < 0.8:
                mean_relative_diff = ((logits_sdpa - logits_eager).abs() / (logits_eager.abs() + 1e-12)).mean()
                raise ValueError(
                    f"mean relative difference for {key}: {mean_relative_diff:.3e}, torch atol = {atol}, torch rtol = "
                    f"{rtol}"
                )