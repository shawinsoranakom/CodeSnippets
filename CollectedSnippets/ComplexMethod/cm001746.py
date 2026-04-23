def _test_eager_matches_sdpa_inference(
    self,
    name,
    dtype,
    padding_side,
    use_attention_mask,
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

    def _can_output_attn(model):
        parameters = inspect.signature(model.forward).parameters
        if "output_attentions" in parameters:
            return True

        kwargs_param = parameters.get("kwargs")
        if kwargs_param is not None:
            try:
                annotation = kwargs_param.annotation.__args__
                return "output_attentions" in annotation[0].__annotations__
            except AttributeError:
                return False
        return False

    for model_class in self.all_model_classes:
        # Set seed for deterministic test - ensures reproducible model initialization and inputs
        set_seed(42)
        config, inputs_dict = self.model_tester.prepare_config_and_inputs_for_common()
        set_config_for_less_flaky_test(config)

        # If it's a model with sliding window attention, let's test it with sliding window
        if hasattr(config, "sliding_window"):
            config.sliding_window = 2

        model = model_class(config)
        # TODO: standardize the interfaces for musicgen models, see other todo in this test
        if model.__class__.__name__ == "MusicgenMelodyForConditionalGeneration":
            is_encoder_decoder = True
        else:
            is_encoder_decoder = model.config.is_encoder_decoder

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

            try:
                model_eager = deepcopy(model_sdpa)
                model_eager.set_attn_implementation("eager")
            except Exception as _:
                model_eager = model_class.from_pretrained(**model_from_pretrained_kwargs, attn_implementation="eager")
            model_eager = model_eager.eval().to(torch_device)

        set_model_for_less_flaky_test(model_eager)
        set_model_for_less_flaky_test(model_sdpa)

        can_output_attn = _can_output_attn(model_sdpa)
        if not (self.has_attentions and can_output_attn) and output_attentions:
            self.skipTest(reason="Model does not support output_attentions")

        # TODO: if we can also check with `batch_size=1` without being flaky?
        for batch_size in [7]:
            # musicgen decoder models; TODO: find better abstraction
            if (
                model.__class__.__name__.startswith("Musicgen")
                and hasattr(self.model_tester, "num_codebooks")
                and not hasattr(model_eager, "text_encoder")
            ):
                input_data_batch_size = batch_size * self.model_tester.num_codebooks
            else:
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

                # extend value to have at least `input_data_batch_size` elements
                if value.shape[0] < input_data_batch_size:
                    size = (input_data_batch_size - value.shape[0], *value.shape[1:])
                    if torch.is_floating_point(value):
                        extension = torch.rand(size=size, dtype=value.dtype, device=torch_device)
                    else:
                        extension = torch.randint(high=5, size=size, dtype=value.dtype, device=torch_device)
                    value = torch.cat((value, extension), dim=0).to(torch_device)

                processed_inputs[key] = value[:input_data_batch_size]

            if not use_attention_mask:
                dummy_attention_mask = None
            else:
                dummy_attention_mask = inputs_dict.get("attention_mask", None)
                if dummy_attention_mask is None:
                    if is_encoder_decoder:
                        seqlen = inputs_dict.get("decoder_input_ids", processed_inputs[model.main_input_name]).shape[
                            -1
                        ]
                    else:
                        seqlen = processed_inputs[model.main_input_name].shape[-1]
                    dummy_attention_mask = torch.ones(batch_size, seqlen).to(torch.int64).to(torch_device)

                # extend dummy_attention_mask to have at least `batch_size` elements
                if dummy_attention_mask.shape[0] < batch_size:
                    size = (batch_size - dummy_attention_mask.shape[0], *dummy_attention_mask.shape[1:])
                    extension = torch.ones(size=size, dtype=dummy_attention_mask.dtype, device=torch_device)
                    dummy_attention_mask = torch.cat((dummy_attention_mask, extension), dim=0)

                dummy_attention_mask = dummy_attention_mask[:batch_size].to(torch_device)

                dummy_attention_mask[:] = 1
                if padding_side == "left":
                    dummy_attention_mask[-1, :2] = 0
                    dummy_attention_mask[-1, 2:] = 1
                elif padding_side == "right":
                    dummy_attention_mask[-1, -2:] = 0
                    dummy_attention_mask[-1, :-2] = 1

            if is_encoder_decoder:
                # musicgen encoder-decoder models; TODO: find better abstraction
                if model.__class__.__name__.startswith("Musicgen") and hasattr(self.model_tester, "num_codebooks"):
                    input_data_batch_size = batch_size * self.model_tester.num_codebooks
                else:
                    input_data_batch_size = batch_size

                decoder_input_ids = inputs_dict.get("decoder_input_ids", processed_inputs[model.main_input_name])
                decoder_input_ids = decoder_input_ids[:input_data_batch_size]
                if decoder_input_ids.shape[0] != input_data_batch_size:
                    extension = torch.ones(
                        input_data_batch_size - decoder_input_ids.shape[0],
                        *decoder_input_ids.shape[1:],
                        dtype=decoder_input_ids.dtype,
                        device=torch_device,
                    )
                    decoder_input_ids = torch.cat((decoder_input_ids, extension), dim=0)
                    decoder_input_ids = decoder_input_ids.to(torch_device)

                # TODO: never an `attention_mask` arg here?
                processed_inputs.update(
                    {
                        "decoder_input_ids": decoder_input_ids,
                        "decoder_attention_mask": dummy_attention_mask,
                        "output_hidden_states": True,
                    }
                )
            else:
                processed_inputs.update(
                    {
                        "output_hidden_states": True,
                    }
                )

                # Otherwise fails for e.g. WhisperEncoderModel
                if "attention_mask" in inspect.signature(model_eager.forward).parameters:
                    processed_inputs["attention_mask"] = dummy_attention_mask

                if self.has_attentions and _can_output_attn(model_sdpa):
                    processed_inputs["output_attentions"] = output_attentions
            if "bool_masked_pos" in inspect.signature(model_eager.forward).parameters:
                dummy_mask = torch.ones((self.model_tester.num_masks,))

                # In case of additional token (like class) we define a custom `mask_length`
                if hasattr(self.model_tester, "mask_length"):
                    mask_length = self.model_tester.mask_length - dummy_mask.size(0)
                else:
                    mask_length = self.model_tester.seq_length - dummy_mask.size(0)
                dummy_mask = torch.cat([dummy_mask, torch.zeros(mask_length)])
                dummy_bool_masked_pos = dummy_mask.expand(batch_size, -1).bool()
                processed_inputs["bool_masked_pos"] = dummy_bool_masked_pos.to(torch_device)

            if "noise" in inspect.signature(model_eager.forward).parameters:
                np.random.seed(2)
                num_patches = int((self.model_tester.image_size // self.model_tester.patch_size) ** 2)
                noise = np.random.uniform(size=(batch_size, num_patches))
                processed_inputs["noise"] = torch.from_numpy(noise)

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

            if "logits_per_text" in outputs_eager:
                key = "logits_per_text"
            elif "vision_hidden_states" in outputs_eager:
                key = "vision_hidden_states"
            elif "audio_values" in outputs_eager:
                key = "audio_values"
            elif "decoder_hidden_states" in outputs_eager:
                key = "decoder_hidden_states"
            elif "logits" in outputs_eager and "Classification" in model_class.__name__:
                key = "logits"
            elif "language_model_outputs" in outputs_eager and "blip" in model_class.__name__.lower():
                outputs_eager = outputs_eager["language_model_outputs"]
                outputs_sdpa = outputs_sdpa["language_model_outputs"]
                key = "hidden_states" if "hidden_states" in outputs_eager else "decoder_hidden_states"
            elif "decoder_output" in outputs_eager and "clipseg" in model_class.__name__.lower():
                outputs_eager = outputs_eager["decoder_output"]
                outputs_sdpa = outputs_sdpa["decoder_output"]
                key = "hidden_states" if "hidden_states" in outputs_eager else "decoder_hidden_states"
            else:
                key = "hidden_states"

            # TODO: rename logits -> hidden_states
            logits_eager = outputs_eager[key]
            logits_sdpa = outputs_sdpa[key]

            if key in ["vision_hidden_states", "decoder_hidden_states", "hidden_states"]:
                logits_eager = logits_eager[-1]
                logits_sdpa = logits_sdpa[-1]

            if key == "logits_per_text":
                nan_mask = torch.isnan(logits_eager)
                logits_eager[nan_mask] = 0
                logits_sdpa[nan_mask] = 0

            if torch_device in ["cpu", "cuda"]:
                atol = atols[torch_device, enable_kernels, dtype]
                rtol = rtols[torch_device, enable_kernels, dtype]
            elif torch_device in ["hpu", "npu"]:
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

            # Masked tokens output slightly deviates - we don't mind that.
            if use_attention_mask:
                _logits_sdpa = torch.zeros_like(input=logits_sdpa)
                _logits_eager = torch.zeros_like(input=logits_eager)

                _logits_sdpa[:-1] = logits_sdpa[:-1]
                _logits_eager[:-1] = logits_eager[:-1]

                if padding_side == "left":
                    _logits_sdpa[-1:, 2:] = logits_sdpa[-1:, 2:]
                    _logits_eager[-1:, 2:] = logits_eager[-1:, 2:]

                elif padding_side == "right":
                    _logits_sdpa[-1:, 2:] = logits_sdpa[-1:, :-2]
                    _logits_eager[-1:, 2:] = logits_eager[-1:, :-2]

                logits_sdpa = _logits_sdpa
                logits_eager = _logits_eager

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