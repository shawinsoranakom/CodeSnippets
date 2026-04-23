def vllm_generation_init_patch():
    # trl moved vllm stuff to trl/generation/vllm_generation.py
    # We need to patch it to not instantiate another vLLM instance if we already have one with fast_inference
    # Edit the TRL source directly and install the patched function in the TRL module.
    # https://github.com/huggingface/trl/commit/0eb66d8f2fc63b3d00d8dbc18f99c3f48750bd16
    # This exists in trl versions 0.28.0 and above

    if importlib.util.find_spec("trl") is None:
        return
    if Version(importlib_version("trl")) < Version("0.28.0"):
        return

    try:
        import trl.generation.vllm_generation as vllm_generation
    except (ImportError, NameError, Exception) as e:
        logger.info(f"Unsloth: Failed to import trl.generation.vllm_generation: {e}")
        return

    def patch_vllm_generation_method(method_name, transform, marker, filename_suffix):
        method = getattr(vllm_generation.VLLMGeneration, method_name, None)
        if method is None:
            logger.info(f"Unsloth: Could not find VLLMGeneration.{method_name}")
            return False

        try:
            src = inspect.getsource(method)
        except Exception as e:
            logger.info(
                f"Unsloth: Could not get source of VLLMGeneration.{method_name}: {e}"
            )
            return False

        src = textwrap.dedent(src)
        if marker in src:
            return True

        src = transform(src)
        filename = f"<unsloth_trl_vllm_generation_{filename_suffix}_patch>"
        source_lines = [line + "\n" for line in src.splitlines()]
        linecache.cache[filename] = (
            len(src),
            None,
            source_lines,
            filename,
        )

        local_ns = {}
        exec(compile(src, filename, "exec"), vllm_generation.__dict__, local_ns)
        setattr(vllm_generation.VLLMGeneration, method_name, local_ns[method_name])
        return True

    # Patch init to remove vLLM.LLM instantiation
    def patch_init_vllm(src):
        pattern = re.compile(
            r"(?P<llm_block>^(?P<indent>[ \t]*)self\.llm\s*=\s*LLM\s*\(\n(?:.*\n)*?^(?P=indent)\))",
            re.MULTILINE,
        )

        def replace_llm_block(match):
            indent = match.group("indent")
            llm_block = textwrap.dedent(match.group("llm_block"))
            return (
                f"{indent}if hasattr(model, 'vllm_engine'):\n"
                f"{indent}    # Unsloth already inits vLLM in fast inference mode. Do not redo :)\n"
                f"{indent}    self.llm = model.vllm_engine\n"
                f"{indent}    self.unsloth_fast_inference_lora = True\n"
                f"{indent}else:\n" + textwrap.indent(llm_block, indent + "    ")
            )

        patched_src, num_replacements = pattern.subn(replace_llm_block, src, count = 1)
        if num_replacements == 0:
            raise RuntimeError(
                "Unsloth: Warning - regex did not match, VLLMGeneration._init_vllm patch may have failed"
            )
        return patched_src

    # has some sync_weights or reload rpc calls.
    # we patched the grpo_trainer to strip them for prev versions
    # Ref: grpo_trainer__generate_single_turn above around L270-280
    def patch_sync_weights(src):
        pattern = re.compile(
            r"^(?P<def_line>def sync_weights\(self\):\n)(?P<body>(?:.*\n)*)",
            re.MULTILINE,
        )

        def replace_sync_weights(match):
            body = match.group("body")
            guard = (
                "    if getattr(self, 'unsloth_fast_inference_lora', False):\n"
                "        # Unsloth fast inference LoRA shares weights with vLLM already.\n"
                "        return\n\n"
            )
            return match.group("def_line") + guard + body

        patched_src, num_replacements = pattern.subn(replace_sync_weights, src, count = 1)
        if num_replacements == 0:
            raise RuntimeError(
                "Unsloth: Warning - regex did not match, VLLMGeneration.sync_weights patch may have failed"
            )
        return patched_src

    def patch_generate(src):
        pattern = re.compile(
            r"^(?P<indent>[ \t]*)self\.llm\.collective_rpc\(\s*(['\"])reload_weights\2\s*\)\s*$",
            re.MULTILINE,
        )

        def replace_reload_weights(match):
            indent = match.group("indent")
            return f'{indent}pass  # self.llm.collective_rpc("reload_weights")'

        patched_src, num_replacements = pattern.subn(
            replace_reload_weights, src, count = 1
        )
        if num_replacements == 0:
            raise RuntimeError(
                "Unsloth: Warning - regex did not match, VLLMGeneration.generate patch may have failed"
            )
        return patched_src

    try:
        init_patched = patch_vllm_generation_method(
            "_init_vllm",
            patch_init_vllm,
            "self.unsloth_fast_inference_lora = True",
            "init_vllm",
        )
        sync_patched = patch_vllm_generation_method(
            "sync_weights",
            patch_sync_weights,
            "if getattr(self, 'unsloth_fast_inference_lora', False):",
            "sync_weights",
        )
        generate_patched = patch_vllm_generation_method(
            "generate",
            patch_generate,
            'pass  # self.llm.collective_rpc("reload_weights")',
            "generate",
        )
    except RuntimeError as e:
        logger.warning(str(e))
        return

    if init_patched:
        logger.info("Unsloth: Patched trl VLLMGeneration._init_vllm")
    if sync_patched:
        logger.info("Unsloth: Patched trl VLLMGeneration.sync_weights")
    if generate_patched:
        logger.info("Unsloth: Patched trl VLLMGeneration.generate")