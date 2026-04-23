def patch_functions(RLTrainer, trainer_file, RLTrainer_name, all_imports, imports):
    init = inspect.getsource(RLTrainer.__init__)
    old_init = init

    # Remove brackets in comments since it interferes ie (...)
    comments = re.findall(r"\#[^\n]{1,}\n", init)
    bracketed_comments = [x for x in comments if "(" in x or ")" in x]
    # Replace with [...] instead
    for bracketed_comment in bracketed_comments:
        init = init.replace(
            bracketed_comment,
            bracketed_comment.replace("(", "[").replace(")", "]"),
        )

    # Remove peft_config
    init = init.replace("elif peft_config is None:", "elif False:")
    init = init.replace("elif peft_config is not None:", "elif False:")
    init = init.replace("if peft_config is None:", "if False:")
    init = init.replace("if peft_config is not None:", "if False:")
    init = init.replace("get_peft_model(model, peft_config)", "model")
    # New TRL 0.20.0
    init = init.replace(
        "if peft_config is not None or (is_peft_available() and isinstance(model, PeftModel)):",
        "if False:",
    )
    # New TRL 0.20.0
    init = init.replace(
        "model = self._prepare_peft_model(model, peft_config, args)\n", "pass\n"
    )
    # TRL 0.22.0+ uses prepare_peft_model as a standalone function
    init = init.replace("model = prepare_peft_model(model, peft_config, args)", "pass")

    # Skip add_adapter("ref") for reference model computation
    # Unsloth: We comment out the "ref" adapter creation because:
    # 1. We want to use the original BASE MODEL as the reference model, not the SFT/LoRA model
    # 2. PEFT doesn't allow multiple adapters when target_parameters is used (MoE models)
    # When "ref" is not in peft_config, GRPO/RLOO fallback uses disable_adapter()
    # which gives the base model logits - exactly what we want
    add_adapter_block_pattern = (
        r"([ \t]*)"  # Capture leading indentation
        r"if\s+is_peft_available\(\)\s+and\s+is_peft_model\(model\)\s+and\s+args\.beta\s*!=\s*0\.0\s*:"
        r"(.*?)"  # Match the entire block until ref_param.data.copy_
        r"ref_param\.data\.copy_\(param\.data\)"
    )

    def comment_out_block(match):
        """Comment out each line in the matched block, preserving indentation."""
        full_match = match.group(0)
        indent = match.group(1)
        lines = full_match.split("\n")
        commented_lines = []
        # Add explanation comment first
        commented_lines.append(
            f"{indent}# Unsloth: Commented out - use base model as reference, not SFT/LoRA model"
        )
        # Comment out each line - insert # after leading whitespace to preserve indentation
        for line in lines:
            if line.strip():
                stripped = line.lstrip()
                leading_ws = line[: len(line) - len(stripped)]
                commented_lines.append(f"{leading_ws}# {stripped}")
            else:
                commented_lines.append(line)
        return "\n".join(commented_lines)

    init = re.sub(add_adapter_block_pattern, comment_out_block, init, flags = re.DOTALL)

    # Set use_vllm if not set
    if "args.use_vllm" in init and "model" in init and "args" in init:
        # .*? matches first match. .+? matches final match.
        replacer = re.findall(
            r"def __init__\(.*?\).*?\:\n",
            init,
            flags = re.MULTILINE | re.DOTALL,
        )
        if len(replacer) != 0:
            replacer = replacer[0]
            vllm_setter = (
                "\n"
                + " " * 8
                + "if hasattr(model, 'vllm_engine') and hasattr(args, 'use_vllm'):\n"
                + " " * 12
                + "if (getattr(args, 'use_vllm', False) == False):\n"
                + " " * 16
                + "args.use_vllm = True\n"
            )
            # " " * 16 + "args.vllm_importance_sampling_correction = True\n" + \
            # " " * 16 + "args.vllm_importance_sampling_cap = 2.0\n"

            if "grpo" in trainer_file and trl_version >= Version("0.18.0"):
                # If model has vllm_engine, then use vllm in colocate mode. Donot wait for server
                vllm_setter += " " * 12 + "args.vllm_mode='colocate'\n"
                if trl_version >= Version("0.23.0"):
                    # We need to set this flag for sleep mode auto working with trl update
                    vllm_setter += (
                        " " * 12
                        + "if os.environ.get('UNSLOTH_VLLM_STANDBY', '0') == '1':\n"
                        + " " * 16
                        + "args.vllm_enable_sleep_mode=True\n"
                    )

            init = init.replace(replacer, replacer + vllm_setter)

    # breakpoint()

    vllm_part = re.findall(
        r"(\n[\s]{8}" r"if (self|args)\.use_vllm\:.*?" r"\n[\s]{8}" "else:\n)",
        init,
        flags = re.MULTILINE | re.DOTALL,
    )

    if len(vllm_part) == 1:
        vllm_part, args = vllm_part[0][0], vllm_part[0][1]
        # Strip all comments
        new_vllm_part = re.sub(
            r"^\s*\#[^\n]*\n?", "", vllm_part, flags = re.MULTILINE
        )  # to also remove whole comment line instead of just starting at #
        new_vllm_part = re.sub(
            r"\s*\#.*$", "", new_vllm_part, flags = re.MULTILINE
        )  # remove comments that occur after code

        # Get SamplingParams
        sampling_params = re.findall(
            r"\n[\s]{4,}(self\.[^\s]{1,}[\s]{0,}\=[\s]{0,}" r"SamplingParams\(.+?\))",
            new_vllm_part,
            flags = re.MULTILINE | re.DOTALL,
        )

        if len(sampling_params) == 1:
            sampling_params = sampling_params[0]
            # Fix guided_decoding
            sampling_params = sampling_params.replace(
                "guided_decoding=guided_decoding,",
                "guided_decoding="
                'GuidedDecodingParams(backend="outlines", regex=args.vllm_guided_decoding_regex) '
                'if getattr(args, "vllm_guided_decoding_regex", None) is not None else None,',
            )
            # Replace with our vLLM engine
            sampling_params = (
                " " * 12
                + "self.llm = model.vllm_engine; self._last_loaded_step = 0; "
                + sampling_params
            )  # Add spaces

            # count the indentation of last line of sampling_params.
            splitted_sampling_params = sampling_params.split("\n")
            if len(splitted_sampling_params) >= 2:
                last_line = splitted_sampling_params[-1]
                last_prev_line = splitted_sampling_params[-2]
                last_prev_indentation = len(last_prev_line) - len(
                    last_prev_line.lstrip()
                )
                last_indentation = len(last_line) - len(last_line.lstrip())

                # Add extra arguments to SamplingParams
                extra = "**getattr(getattr(args, 'vllm_sampling_params', vLLMSamplingParams()), '_set_kwargs', {})"
                # Backwards replace
                to_replace = (
                    ",\n"
                    + " " * last_prev_indentation
                    + extra
                    + ",\n"
                    + " " * last_indentation
                    + ")"
                )
                sampling_params = to_replace.join(sampling_params.rsplit(")", 1))
                # Strip multiple commas
                sampling_params = re.sub(r"[\,][\s]{0,}\,", ",", sampling_params)

                new_vllm_part = (
                    f"\n{' ' * 8}if {args}.use_vllm:\n{sampling_params}"
                    f"\n{' ' * 8}else:\n"
                )

        if trl_version >= Version("0.18.0"):
            # Replace LLM init with already existing vLLM engine for colocate mode
            vllm_llm_init_pattern = r"self\.llm\s*=\s*LLM\(.*?\)*\)\s*?\n(?!,)"
            vllm_llm_replacement = "self.llm = model.vllm_engine\n"
            new_vllm_part = re.sub(
                vllm_llm_init_pattern,
                vllm_llm_replacement,
                new_vllm_part,
                flags = re.DOTALL,  # Ensure . matches newlines [[5]]
            )

        init = init.replace(vllm_part, new_vllm_part)

    # Search for vLLM calling in all child functions
    functions = dir(RLTrainer)
    RLTrainer_source = inspect.getsource(RLTrainer)
    functions = [x for x in functions if f"def {x}" in RLTrainer_source]

    changed = {
        "__init__": (
            old_init,
            init,
        )
    }
    edit_functions = RL_FUNCTIONS.get(trainer_file, [])

    for function in functions:
        if not hasattr(RLTrainer, function):
            continue
        if function in changed:
            original_source, source = changed[function]
        else:
            fx = getattr(RLTrainer, function)
            try:
                source = inspect.getsource(fx)
            except:
                continue
            original_source = source

        # Check for function
        for edit_function in edit_functions:
            source = edit_function(function, source)

        """
        import torch
        X = torch.ones((2, 2048, 201088), dtype = torch.bfloat16, device = "cuda")
        X[torch.randperm(2, dtype = torch.int64, device = X.device)]

        will error out in torch 2.8 AcceleratorError: CUDA error: invalid configuration argument
        """
        source = re.sub(
            r"(\n[\s]{4,})generation_batch = shuffle_sequence_dict\(generation_batch\)\n",
            r"\n\1try: generation_batch = shuffle_sequence_dict(generation_batch)\n\1except: pass\n",
            source,
        )

        # llm_model = self.llm.llm_engine.model_executor.driver_worker.model_runner.model
        source = re.sub(
            r"(\n[\s]{4,}).+?model_executor\.driver_worker.+?\n",
            r"\n\1pass\n",
            source,
        )

        # llm_model.load_weights(model.state_dict().items())
        source = re.sub(
            r"(\n[\s]{4,}).+?load_weights\(.+?\n",
            r"\n\1pass\n",
            source,
        )

        # .state_dict()
        source = re.sub(
            r"\.state_dict\(\)",
            r"",
            source,
        )

        # Replace self.llm.generate and self.llm.chat
        if "CUDA_VISIBLE_DEVICES" in os.environ:
            lora_name = (
                trainer_file
                + "_lora_model_' + "
                + "(os.environ.get('CUDA_VISIBLE_DEVICES', '0').replace(',',''))"
            )
        else:
            lora_name = trainer_file + "_lora_model'"
        source = re.sub(
            r"(self\.llm\.(?:generate|chat)\([^\)]{1,})\)",
            r"\1, lora_request = self.model.load_lora('"
            + lora_name
            + r", load_tensors = True))",
            source,
        )
        # All these are to fix multiple commas before lora_request (in case the original code ends with something like ",)")
        # https://github.com/huggingface/trl/blob/main/trl/trainer/grpo_trainer.py#L1388 for eg has such an ending
        source = re.sub(r"\,[\s]{1,}\,[\s]{0,}lora_request", ", lora_request", source)
        source = re.sub(r"[\s]{1,}\,[\s]{0,}lora_request", ", lora_request", source)
        source = re.sub(r"[\,]{1,}[\s]{0,}lora_request", ", lora_request", source)
        # Prefer using unsloth's sampling params and fallback to trl's if not found
        # We'll enable this later separately when combining both this and GRPOConfig params
        # source = re.sub(
        #     r"sampling_params\s*=\s*sampling_params",
        #     r"sampling_params = getattr(self.args, 'vllm_sampling_params', sampling_params)",
        #     source
        # )
        # Fix later versions of SamplingParams via grpo_update_SamplingParams
        source = source.replace(
            "sampling_params = SamplingParams(**generation_kwargs)",
            "sampling_params = SamplingParams("
            "**grpo_update_SamplingParams("
            "SamplingParams, generation_kwargs, "
            "getattr(self.args, 'vllm_sampling_params', None)"
            ")"
            ")",
        )

        # Skip if no changes done
        if source == original_source:
            continue

        # Find all imports
        imports += [x for x in all_imports if not x.startswith("_") and x in source]

        changed[function] = (
            original_source,
            source,
        )

    # Import all functions
    imports = list(set(imports))

    # Patch all functions
    for function in changed:
        old, new = changed[function]
        RLTrainer_source = RLTrainer_source.replace(old, new)

    RLTrainer_source = RLTrainer_source.replace(
        f"class {RLTrainer_name}", f"class _Unsloth{RLTrainer_name}", 1
    )
    return RLTrainer_source