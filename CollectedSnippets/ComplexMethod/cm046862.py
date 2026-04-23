def patch_sft_trainer_tokenizer():
    """
    Patches the trainer with changes
    """
    try:
        sft_trainer = eval(f"trl.trainer.sft_trainer.SFTTrainer")
    except:
        return
    all_imports = dir(trl.trainer.sft_trainer)

    for (
        function_name,
        replacer,
    ) in (
        # ("_prepare_non_packed_dataloader", "def tokenize(element):",),
        (
            "_prepare_non_packed_dataloader",
            None,
        ),
        (
            "_prepare_dataset",
            None,
        ),
        # ("_prepare_packed_dataloader", "if dataset_text_field is not None",),
    ):
        if not hasattr(sft_trainer, function_name):
            continue

        function = getsource(eval(f"sft_trainer.{function_name}"))
        where = function.find("def")
        function = function.split("\n")
        function = "\n".join(x[where:] for x in function)

        check_text = (
            "\n"
            "if 'tokenizer'          not in locals(): tokenizer = processing_class\n"
            "if 'formatting_func'    not in locals(): raise RuntimeError('Unsloth: Please file a bug report - `formatting_func` does not exist!')\n"
            "if 'dataset_text_field' not in locals() and 'args' in locals(): dataset_text_field = args.dataset_text_field\n"
            "if 'dataset_text_field' not in locals(): dataset_text_field = None\n"
            "if formatting_func is None and dataset_text_field is None and 'prompt' in dataset[0] and 'completion' in dataset[0]:\n"
            "    test_text = (dataset[0]['prompt'] + dataset[0]['completion']) if (isinstance(dataset[0]['prompt'], str) and isinstance(dataset[0]['completion'], str)) else None\n"
            "elif formatting_func is None and dataset_text_field is not None:\n"
            "    test_text = dataset[0][dataset_text_field]\n"
            "elif formatting_func is not None:\n"
            "    test_text = formatting_func(dataset[0])[0]\n"
            "else:\n"
            "    test_text = None\n"
            "chat_template = getattr(tokenizer, 'chat_template', None)\n"
            "chat_template = '' if chat_template is None else chat_template\n"
            "has_bos_token_already = ((test_text is not None and test_text.startswith(tokenizer.bos_token)) or tokenizer.bos_token in chat_template) "
            "if getattr(tokenizer, 'bos_token', None) is not None else False\n"
            "if 'add_special_tokens' not in locals() and has_bos_token_already:\n"
            "    from functools import partial\n"
            "    tokenizer = partial(tokenizer, add_special_tokens = False)\n"
            "    processing_class = tokenizer\n"
            "else:\n"
            "    add_special_tokens = False if has_bos_token_already else add_special_tokens\n\n"
        )

        check_text = check_text.split("\n")
        check_text = "\n".join(" " * where + x for x in check_text)
        check_text = check_text.rstrip() + "\n"

        if replacer is None:
            # .*? matches first match. .+? matches final match.
            replacer = re.findall(
                f"def {function_name}" + r"\(.*?\).*?\:\n",
                function,
                flags = re.MULTILINE | re.DOTALL,
            )
            if len(replacer) == 0:
                continue
            replacer = replacer[0]
            function = function.replace(replacer, replacer + check_text)
        else:
            function = function.replace(replacer, check_text + replacer)

        x = [x for x in all_imports if x in function]
        try:
            exec(f"from trl.trainer.sft_trainer import ({','.join(x)})", locals())
        except ImportError:
            for _item in x:
                try:
                    exec(f"from trl.trainer.sft_trainer import {_item}", locals())
                except ImportError:
                    pass
        exec(function, locals(), globals())
        exec(
            f"trl.trainer.sft_trainer.SFTTrainer.{function_name} = {function_name}",
            globals(),
        )

    # Patch train with fix_untrained_tokens
    for path_to_trainer in (
        "sft_trainer.SFTTrainer",
        "dpo_trainer.DPOTrainer",
        "kto_trainer.KTOTrainer",
    ):
        function_name, replacer = "train", "if resume_from_checkpoint is False:"
        try:
            function = getsource(eval(f"trl.trainer.{path_to_trainer}.{function_name}"))
        except Exception:
            continue
        where = function.find("def")
        function = function.split("\n")
        function = "\n".join(x[where:] for x in function)

        check_text = (
            "\n"
            "import subprocess, re, gc, numpy as np\n"
            "a = np.array([0,])\n"
            "try:\n"
            "    a = subprocess.check_output('nvidia-smi --query-gpu=memory.used --format=csv', shell = True)\n"
            "    a = re.findall(rb'([\\d]{1,})[\\s]{1,}M', a)\n"
            "    a = np.array([int(x.decode('utf-8'))/1024 for x in a])\n"
            "except:\n"
            "    if not torch.cuda.is_available():\n"
            "        raise RuntimeError('Unsloth: No GPU detected. AMD ROCm users: install ROCm-enabled PyTorch -- see https://docs.unsloth.ai/get-started/install-and-update/amd')\n"
            "    # nvidia-smi unavailable but torch.cuda IS available -- we are on\n"
            "    # a ROCm host (ROCm reuses the torch.cuda.* API surface, so\n"
            "    # device_count() is authoritative) or on a CUDA host without\n"
            "    # the CLI installed. Use the device count directly as a\n"
            "    # conservative multi-GPU signal: any configuration with more\n"
            "    # than one visible device is flagged as unsupported, matching\n"
            "    # the spirit of the per-device memory check used on CUDA.\n"
            "    if torch.cuda.device_count() > 1:\n"
            "        raise RuntimeError('Unsloth currently does not support multi GPU setups - but we are working on it!')\n"
            "if ((a - PRE_CHECK) >= 1).sum() > 1:\n"
            "    raise RuntimeError('Unsloth currently does not support multi GPU setups - but we are working on it!')\n"
            "for _ in range(3):\n"
            "    gc.collect()\n"
            "    torch.cuda.empty_cache()\n"
            "pass\n"
            "\n"
            "tokenizer = self.processing_class if hasattr(self, 'processing_class') else self.tokenizer\n"
            "fix_untrained_tokens(self.model, tokenizer, self.train_dataset, IGNORED_TOKENIZER_NAMES, eps = 1e-16)\n\n"
            "fix_zero_training_loss(self.model, tokenizer, self.train_dataset)\n\n"
        )

        # Warn on gradient accumulation steps if it's used
        check_text += (
            "\n"
            "try:\n"
            "    gradient_accumulation_steps = self.args.gradient_accumulation_steps\n"
            "    if type(gradient_accumulation_steps) is int and gradient_accumulation_steps > 1:\n"
            "        from transformers import __version__ as transformers_version\n"
            "        from packaging.version import Version\n"
            "        if Version(transformers_version) <= Version('4.45.2'):\n"
            "            print('**** Unsloth: Please use our fixed gradient_accumulation_steps by updating transformers, TRL and Unsloth!\\n'\\\n"
            "                  '`pip install --upgrade --no-cache-dir --no-deps unsloth transformers git+https://github.com/huggingface/trl.git`')\n"
            "except:\n"
            "    pass\n"
            "\n\n"
        )

        # Add NEFTune since it doesn't seem to work?? We need to manually inject it
        check_text += (
            "\n"
            "if hasattr(self, 'neftune_hook_handle'):\n"
            "    self.neftune_hook_handle.remove()\n"
            "    if hasattr(self, 'neftune_hook_handle'): del self.neftune_hook_handle\n"
            "\n"
            "if getattr(self, 'neftune_noise_alpha', None) is not None:\n"
            "    self.model.get_input_embeddings().neftune_noise_alpha = self.neftune_noise_alpha\n"
            "    self.neftune_hook_handle = self.model.get_input_embeddings().register_forward_hook(neftune_post_forward_hook)\n"
            "pass\n"
            "\n"
        )

        # Also DPO weirdly tokenizes non numeric columns? Delete them!
        check_text += (
            "\n"
            "if hasattr(self.train_dataset, 'column_names'):\n"
            "    column_names = set(self.train_dataset.column_names)\n"
            "    check = ['chosen', 'rejected', 'prompt', 'chosen_input_ids', 'chosen_attention_mask',\n"
            "        'chosen_labels', 'rejected_input_ids', 'rejected_attention_mask', 'rejected_labels',\n"
            "        'prompt_input_ids', 'prompt_attention_mask']\n"
            "    if all(x in column_names for x in check):\n"
            "        self.train_dataset = self.train_dataset.remove_columns(['chosen', 'rejected', 'prompt'])\n"
            "    del check, column_names\n"
            "\n"
        )

        check_text = check_text.split("\n")
        check_text = "\n".join(" " * where + x for x in check_text)

        function = function.replace(replacer, check_text + replacer)
        exec(function, globals())

        exec(
            f"trl.trainer.{path_to_trainer}.{function_name} = {function_name}",
            globals(),
        )