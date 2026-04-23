def grpo_trainer__generate_and_score_completions(function_name, function):
    if function_name != "_generate_and_score_completions":
        return function

    # TRL 0.19.0 did skip_special_tokens = True which should be False
    function = function.replace(
        "prompt_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False",
        "prompt_ids, skip_special_tokens=False, clean_up_tokenization_spaces=False",
    )

    # Left pad prompt before calculation old and ref hidden states
    line_to_replace = 'batch_size = self.args.per_device_train_batch_size if mode == "train" else self.args.per_device_eval_batch_size'

    # The new multi-line string that will replace the line above
    replacement_lines = """
        max_left_pad = None
        batch_size = self.args.per_device_train_batch_size if mode == "train" else self.args.per_device_eval_batch_size
        try:
            # TRL 0.23.1 and below path
            if not has_images:
                # Left pad prompt before calculation old and ref hidden states
                left_pad_tokens_per_prompt = calculate_pad_tokens_in_prompt(prompt_completion_ids, logits_to_keep, self.processing_class.pad_token_id)
                max_left_pad = torch.max(left_pad_tokens_per_prompt).item()
        except:
            # TRL 0.24.0 and below path
            if images is None:
                # Left pad prompt before calculation old and ref hidden states
                left_pad_tokens_per_prompt = calculate_pad_tokens_in_prompt(prompt_completion_ids, logits_to_keep, self.processing_class.pad_token_id)
                max_left_pad = torch.max(left_pad_tokens_per_prompt).item()
        self.model.for_training()"""

    function = function.replace(line_to_replace, replacement_lines)

    pattern_to_find = re.compile(
        r"^\s*if self\.args\.gradient_accumulation_steps % generate_every != 0 or \(\s*"
        r"self\.use_vllm and self\.vllm_importance_sampling_correction\s*"
        r"\):",
        re.MULTILINE,
    )

    replacement_text = """
            if self.args.gradient_accumulation_steps % generate_every != 0 or (
                self.use_vllm
            ):"""
    # Use re.sub() to perform the replacement
    function, num_replacements = pattern_to_find.subn(replacement_text, function)

    pattern_to_find = re.compile(
        r"(^\s*)all_logprobs = \["  # Capture indentation (group 1)
        r".*?"  # Match everything inside non-greedily
        r"for output in outputs\.outputs\s*"
        r"\]",
        re.DOTALL | re.MULTILINE,
    )

    # sanitize_logprob is injected as a module-level function via RLTrainer_replacement
    # template in rl.py (from RL_REPLACEMENTS), so just reference it directly here.
    replacement_text = (
        r"\1all_logprobs = [\n"
        r"\1    [sanitize_logprob(next(iter(logprob.values()))) for logprob in output.logprobs]\n"
        r"\1    for outputs in all_outputs\n"
        r"\1    for output in outputs.outputs\n"
        r"\1]"
    )

    function, num_replacements = pattern_to_find.subn(replacement_text, function)

    # Always between max_prompt_length and use_vllm
    found = re.findall(
        r"\n(([ ]{8,})if self\.max_prompt_length is not None:.*?"
        r"\2if self\.use_vllm:)",
        function,
        flags = re.DOTALL | re.MULTILINE,
    )
    if len(found) != 0:
        replace_part, spacing = found[0]
        removed_comments = re.sub(r"\#[^\n]{1,}", "", replace_part)
        splits = removed_comments.split("\n")
        if (
            sum(re.match(rf"{spacing}[^\s]", x) is not None for x in splits) == 2
            and len(spacing) >= 8
        ):
            new_replacement = f"""\n{spacing}if self.max_prompt_length is not None:
            # If max_prompt_length is set, we trim the prompt to keep only the last `max_prompt_length` tokens.
            # Then we decode those tokens back into text. We manually remove leading pad tokens from the decoded text,
            # because we can't use `skip_special_tokens=True` (some special tokens are still needed for generation).
            protected = [self.image_token_id, self.vision_start_token_id, self.vision_end_token_id]
            protected = [token for token in protected if token is not None]
            prompt_ids, prompt_mask = truncate_with_protected_tokens(
                prompt_ids, prompt_mask, self.max_prompt_length, protected
            )

            prompts_text = [re.sub(rf"^({{re.escape(self.pad_token)}})+", "", text) for text in prompts_text]

            # The chat template inserts a single image token into the prompt text. However, when this text is later
            # tokenized, the single image token string is expanded into multiple image token IDs, depending on the
            # image size. Since we're detokenizing here, we may see repeated image tokens in the decoded text. We
            # collapse them back into a single token string to match the original template.
            if self.image_token is not None:
                prompts_text = [
                    re.sub(rf"({{re.escape(self.image_token)}})+", self.image_token, text) for text in prompts_text
                ]
        # Generate completions using either vLLM or regular generation
        if self.use_vllm:"""
            function = function.replace(replace_part, new_replacement)

    # Important note: we disable TRL's importance sampling logic
    # It is disabled because the LLM path moves left padding to the right.
    # We must adjust the vLLM sampling_logprob tensor in Unsloth to account for this.
    string_to_find = "if self.use_vllm and self.vllm_importance_sampling_correction:"

    replacement_string = (
        "if False and self.use_vllm and self.vllm_importance_sampling_correction:"
    )

    function = function.replace(string_to_find, replacement_string)

    string_to_find = """        if "image_sizes" in prompt_inputs:
            output["image_sizes"] = prompt_inputs["image_sizes"]"""

    replacement_string = """        if "image_sizes" in prompt_inputs:
            output["image_sizes"] = prompt_inputs["image_sizes"]
        if max_left_pad is not None:
            output["max_left_pad"] = torch.tensor(prompt_ids.shape[0] * [max_left_pad]).unsqueeze(-1)
        try:
            if self.use_vllm and getattr(self, "vllm_importance_sampling_correction", False):
                output["sampling_per_token_logps"] = sampling_per_token_logps
        except NameError:
            output["sampling_per_token_logps"] = None"""

    function = function.replace(string_to_find, replacement_string)

    # TRL 0.24.0+ extracts prompts = [x["prompt"] for x in inputs], losing metadata
    # like reasoning_effort. Inject code to store per-sample chat_template_kwargs on self.
    _metadata_extraction = (
        "\n"
        "        # Unsloth: Extract per-sample chat_template_kwargs before metadata is lost\n"
        "        _ct_ = getattr(self.processing_class, 'chat_template', None) or ''\n"
        "        _sk_ = {'prompt', 'chosen', 'rejected', 'completion', 'messages', 'label',\n"
        "                'images', 'image', 'videos', 'video', 'audios', 'audio'}\n"
        "        self._unsloth_batch_chat_kwargs = []\n"
        "        for _inp_ in inputs:\n"
        "            _kw_ = {}\n"
        "            if isinstance(_inp_, dict):\n"
        "                for _k_ in _inp_.keys() - _sk_:\n"
        "                    if _k_ in _ct_ and isinstance(_inp_[_k_], str):\n"
        "                        _kw_[_k_] = _inp_[_k_]\n"
        "            self._unsloth_batch_chat_kwargs.append(_kw_)\n"
    )
    # Insert after: prompts = [x["prompt"] for x in inputs]
    _target_line = 'prompts = [x["prompt"] for x in inputs]'
    if _target_line in function:
        function = function.replace(
            _target_line,
            _target_line + _metadata_extraction,
        )

    # This path is for TRL 0.24.0 images is a variable exclusive to this version
    string_to_find = """        if images is not None:
            output["num_images"] = num_images"""

    replacement_string = """        if images is not None:
            output["num_images"] = num_images
        if max_left_pad is not None:
            output["max_left_pad"] = torch.tensor(prompt_ids.shape[0] * [max_left_pad]).unsqueeze(-1)
        try:
            if self.use_vllm and getattr(self, "vllm_importance_sampling_correction", False):
                output["sampling_per_token_logps"] = sampling_per_token_logps
        except NameError:
            output["sampling_per_token_logps"] = None"""

    function = function.replace(string_to_find, replacement_string)

    if trl_version >= Version("0.24.0"):
        # We replace the call using 'completions' with one using 'completions_text'
        string_to_find = "        rewards_per_func = self._calculate_rewards(inputs, prompts, completions, completion_ids_list)"
        replacement_string = (
            "        if images is not None:\n"
            "            rewards_per_func = self._calculate_rewards(inputs, prompts_text, completions_text, completion_ids_list)\n"
            "        else:\n"
            "            rewards_per_func = self._calculate_rewards(inputs, prompts, completions, completion_ids_list)"
        )
        function = function.replace(string_to_find, replacement_string)

    if "wake_up()" not in function:
        # Sleep functionality has been added to trl in v0.23.0. We do not want to redo this.
        # https://github.com/huggingface/trl/commit/edbe8234bc7e528f72ac76607de9d3e4753e2709

        pattern = re.compile(r".*self\.llm\.generate\(.*\).*", re.MULTILINE)
        matches = list(pattern.finditer(function))
        patched = function

        # Generally there's only one match. But this is just to make sure we don't miss any.
        for match in reversed(matches):
            line = match.group(0)
            indent_match = re.match(r"(\s*)", line)
            indent = indent_match.group(1) if indent_match else ""

            wrapped = (
                f"{indent}if hasattr(self, 'llm'):\n"
                f"{indent}    if getattr(self.llm.llm_engine.vllm_config.model_config, 'enable_sleep_mode', False):\n"
                f"{indent}        self.llm.wake_up()\n"
                f"{line}\n\n"
                f"{indent}if hasattr(self, 'llm'):\n"
                f"{indent}    if getattr(self.llm.llm_engine.vllm_config.model_config, 'enable_sleep_mode', False):\n"
                f"{indent}        self.llm.sleep(os.environ.get('VLLM_SLEEP_MODE', 1))\n"
            )

            patched = patched[: match.start()] + wrapped + patched[match.end() :]

        function = patched

    # Transformers 5.x: Extend mm_token_type_ids for completion tokens (Qwen3VL M-RoPE).
    # TRL handles token_type_ids but not mm_token_type_ids.
    _tt_search = (
        'if "token_type_ids" in forward_kwargs:\n'
        '            token_type_ids = forward_kwargs["token_type_ids"]\n'
        '            forward_kwargs["token_type_ids"] = torch.cat(\n'
        "                [token_type_ids, token_type_ids.new_zeros(completion_ids.shape)], dim=1\n"
        "            )"
    )
    _tt_replace = (
        _tt_search + "\n"
        '        if "mm_token_type_ids" in forward_kwargs:\n'
        '            mm_tti = forward_kwargs["mm_token_type_ids"]\n'
        '            forward_kwargs["mm_token_type_ids"] = torch.cat(\n'
        "                [mm_tti, mm_tti.new_zeros(completion_ids.shape)], dim=1\n"
        "            )"
    )
    function = function.replace(_tt_search, _tt_replace)

    # Save mm_token_type_ids to output dict alongside token_type_ids
    _save_search = (
        'if "token_type_ids" in forward_kwargs:\n'
        '            output["token_type_ids"] = forward_kwargs["token_type_ids"]'
    )
    _save_replace = (
        _save_search + "\n"
        '        if "mm_token_type_ids" in forward_kwargs:\n'
        '            output["mm_token_type_ids"] = forward_kwargs["mm_token_type_ids"]'
    )
    function = function.replace(_save_search, _save_replace)

    return function