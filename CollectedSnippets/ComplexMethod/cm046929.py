def _patch_trl_rl_trainers(trainer_file = "grpo_trainer"):
    # Patch for vLLM and Unsloth PEFT
    import trl
    import trl.trainer

    try:
        trainer = eval(f"trl.trainer.{trainer_file}")
    except Exception as error:
        logger.info(f"Unsloth: Could not import trl.trainer.{trainer_file}: {error}")
        return

    # Get SFTTrainer and SFTConfig names
    name = [
        x
        for x in dir(trainer)
        if x.endswith("Trainer")
        and x != "Trainer"
        and not x.startswith("_")
        and trainer_file.split("_")[0] in x.lower()
    ]
    config = [
        x
        for x in dir(trainer)
        if x.endswith("Config")
        and x != "Config"
        and not x.startswith("_")
        and trainer_file.split("_")[0] in x.lower()
    ]
    if len(name) != 1:
        logger.info(
            f"Unsloth: Could not find Trainer class in trl.trainer.{trainer_file}. Found: {name}"
        )
        return
    if len(config) != 1:
        # TRL 0.26+: Config may be in a separate *_config.py module
        config_module_name = trainer_file.replace("_trainer", "_config")
        try:
            config_mod = eval(f"trl.trainer.{config_module_name}")
            config = [
                x
                for x in dir(config_mod)
                if x.endswith("Config")
                and x != "Config"
                and not x.startswith("_")
                and trainer_file.split("_")[0] in x.lower()
            ]
        except Exception:
            pass
    if len(config) != 1 and len(name) == 1:
        # Thin wrapper fallback: walk the Trainer's MRO to find Config
        # in the real implementation module (e.g., trl.experimental.bco)
        try:
            _temp_cls = eval(f"trl.trainer.{trainer_file}.{name[0]}")
            for _parent in _temp_cls.__mro__[1:]:
                if _parent is object:
                    continue
                _parent_mod = inspect.getmodule(_parent)
                if (
                    _parent_mod is None
                    or _parent_mod.__name__ == f"trl.trainer.{trainer_file}"
                ):
                    continue
                config = [
                    x
                    for x in dir(_parent_mod)
                    if x.endswith("Config")
                    and x != "Config"
                    and not x.startswith("_")
                    and trainer_file.split("_")[0] in x.lower()
                ]
                if len(config) == 1:
                    break
        except Exception:
            pass
    if len(config) != 1:
        logger.info(
            f"Unsloth: Could not find Config class in trl.trainer.{trainer_file}. Found: {config}"
        )
        return

    # Get SFTTrainer, SFTConfig
    RLTrainer_name = name[0]
    RLConfig_name = config[0]
    try:
        RLTrainer = eval(f"trl.trainer.{trainer_file}.{RLTrainer_name}")
    except Exception as e:
        logger.info(
            f"Unsloth: Could not load {RLTrainer_name} from trl.trainer.{trainer_file}: {e}"
        )
        return
    _config_resolved_module = None
    try:
        RLConfig = eval(f"trl.trainer.{trainer_file}.{RLConfig_name}")
    except Exception:
        # TRL 0.26+: Config may be in a separate *_config.py module
        try:
            config_module_name = trainer_file.replace("_trainer", "_config")
            RLConfig = eval(f"trl.trainer.{config_module_name}.{RLConfig_name}")
        except Exception:
            # Thin wrapper fallback: load Config from parent trainer's module
            _config_loaded = False
            try:
                _temp_cls = eval(f"trl.trainer.{trainer_file}.{name[0]}")
                for _parent in _temp_cls.__mro__[1:]:
                    if _parent is object:
                        continue
                    _parent_mod = inspect.getmodule(_parent)
                    if (
                        _parent_mod is None
                        or _parent_mod.__name__ == f"trl.trainer.{trainer_file}"
                    ):
                        continue
                    if hasattr(_parent_mod, RLConfig_name):
                        RLConfig = getattr(_parent_mod, RLConfig_name)
                        _config_resolved_module = _parent_mod
                        _config_loaded = True
                        break
            except Exception:
                pass
            if not _config_loaded:
                logger.info(f"Unsloth: Could not load {RLConfig_name}")
                return

    # Check name
    if RLTrainer.__name__.startswith("Unsloth"):
        print(f"Unsloth: {RLTrainer.__name__} is already patched.")
        return
    if RLConfig.__name__.startswith("Unsloth"):
        print(f"Unsloth: {RLConfig.__name__} is already patched.")
        return

    # TRL 0.26+: Resolve thin wrappers to their experimental parent class.
    # Thin wrappers are deprecation shims in trl.trainer that just forward
    # *args/**kwargs to the real implementation in trl.experimental.
    # Only resolve if a parent class actually lives in a trl.experimental module.
    _trainer_resolved_module = None
    try:
        _trainer_src = inspect.getsource(RLTrainer)
        _trainer_module = inspect.getmodule(RLTrainer)
        _trainer_module_src = (
            inspect.getsource(_trainer_module) if _trainer_module else ""
        )
        if (
            "trl.experimental" in _trainer_src
            or "trl.experimental" in _trainer_module_src
        ):
            for _parent in RLTrainer.__mro__[1:]:
                if _parent is object:
                    continue
                _parent_mod = inspect.getmodule(_parent)
                if _parent_mod is None:
                    continue
                # Only resolve to a parent that lives in trl.experimental
                if "trl.experimental" in _parent_mod.__name__:
                    RLTrainer = _parent
                    _trainer_resolved_module = _parent_mod
                    break
    except Exception:
        pass

    try:
        _config_src = inspect.getsource(RLConfig)
        _config_module = inspect.getmodule(RLConfig)
        _config_module_src = inspect.getsource(_config_module) if _config_module else ""
        if (
            "trl.experimental" in _config_src
            or "trl.experimental" in _config_module_src
        ):
            for _parent in RLConfig.__mro__[1:]:
                if _parent is object:
                    continue
                _parent_mod = inspect.getmodule(_parent)
                if _parent_mod is None:
                    continue
                # Only resolve to a parent that lives in trl.experimental
                if "trl.experimental" in _parent_mod.__name__:
                    RLConfig = _parent
                    break
    except Exception:
        pass

    # Get old source
    old_RLTrainer_source = inspect.getsource(RLTrainer)
    old_RLConfig_source = inspect.getsource(RLConfig)

    if _trainer_resolved_module is not None:
        all_imports = dir(_trainer_resolved_module)
    elif _config_resolved_module is not None:
        all_imports = dir(_config_resolved_module)
    else:
        all_imports = dir(trainer)
    # Fix _deprecate_arguments not getting imported so stop __ but not _
    imports = [x for x in all_imports if not x.startswith("__")]

    # Get default arguments
    EMPTY = inspect.Parameter.empty
    processed = []
    for RLobject in [RLTrainer, RLConfig]:
        parameters = inspect.signature(RLobject.__init__).parameters
        types = (
            bool,
            type(None),
            int,
            float,
            str,
        )
        arguments = ["self"]
        call_args = []
        for k, v in parameters.items():
            if k == "self":
                continue
            v = v.default
            if v == "\n":
                v = re.escape("\n")
            if v is EMPTY:
                arguments.append(k)
            elif type(v) is str:
                arguments.append(f"{k} = '{v}'")
            elif type(v) in types:
                arguments.append(f"{k} = {v}")
            else:
                continue
            call_args.append(f"{k} = {k}")
        arguments = f"\n{' ' * 8}" + f",\n{' ' * 8}".join(arguments)
        call_args = f"\n{' ' * 12}" + f",\n{' ' * 12}".join(call_args)
        processed.append(
            (
                arguments,
                call_args,
            )
        )

    # Process RLTrainer first
    arguments, call_args = processed[0]
    RLTrainer_post = ""

    # Add tokenizer if not seen
    if "tokenizer" not in parameters and "processing_class" in parameters:
        arguments += f",\n{' ' * 8}tokenizer = None"
        call_args = call_args.replace(
            "processing_class = processing_class",
            "processing_class = tokenizer if tokenizer is not None else processing_class",
        )

    # Edit bf16, fp16 by checking model's dtype/torch_dtype directly
    extra_args = ""
    if "args" in call_args and "model" in call_args:
        mixed_precision = (
            "use_bf16 = getattr(args, 'bf16', False)\n"
            "if type(use_bf16) is not bool: use_bf16 = False\n"
            "use_fp16 = getattr(args, 'fp16', False)\n"
            "if type(use_fp16) is not bool: use_fp16 = False\n"
            "force_float32 = False\n"
            "full_finetuning = os.environ.get('UNSLOTH_ENABLE_FULL_FINETUNING', '0') == '1'\n"
            "if not full_finetuning and (os.environ.get('UNSLOTH_FORCE_FLOAT32', '0') == '1'):\n"
            "    print('Unsloth: Switching to float32 training since model cannot work with float16')\n"
            "    force_float32 = True\n"
            "mixed_precision_dtype = os.environ.get('UNSLOTH_MIXED_PRECISION', 'float32')\n"
            "dtype = getattr(model.config, 'dtype', None) or getattr(model.config, 'torch_dtype', None)\n"
            "if dtype is None: dtype = model.get_input_embeddings().weight.dtype\n"
            "from unsloth_zoo.utils import _get_dtype\n"
            "dtype = _get_dtype(dtype)\n"
            "float16 = dtype == torch.float16\n"
            "if not force_float32 and (float16 and use_bf16): raise TypeError('Unsloth: Model is in float16 precision but you want to use bfloat16 precision. Set fp16 to `True` and bf16 to `False`')\n"
            "if not force_float32 and (not float16 and use_fp16): raise TypeError('Unsloth: Model is in bfloat16 precision but you want to use float16 precision. Set fp16 to `False` and bf16 to `True`')\n"
            "if force_float32:\n"
            "    # Forced float32 training\n"
            "    args.fp16 = False\n"
            "    args.bf16 = False\n"
            "    os.environ['ACCELERATE_MIXED_PRECISION'] = 'no'\n"
            "    if hasattr(args, 'mixed_precision'): args.mixed_precision = 'no'\n"
            "    # args.mixed_precision is a new argument which needs to be set now\n"
            "elif (not use_bf16 and not use_fp16) and mixed_precision_dtype == 'float32':\n"
            "    # Mixed precision training\n"
            "    args.fp16 = float16\n"
            "    args.bf16 = not float16\n"
            "    os.environ['ACCELERATE_MIXED_PRECISION'] = 'fp16' if float16 else 'bf16'\n"
            "    if hasattr(args, 'mixed_precision'): args.mixed_precision = 'fp16' if float16 else 'bf16'\n"
            "    # args.mixed_precision is a new argument which needs to be set now\n"
            "elif mixed_precision_dtype == 'bfloat16':\n"
            "    # Both False since bfloat16 full finetuning doesn't do any autocasting.\n"
            "    args.fp16 = False\n"
            "    args.bf16 = False\n"
            "    os.environ['ACCELERATE_MIXED_PRECISION'] = 'no'\n"
            "    if hasattr(args, 'mixed_precision'): args.mixed_precision = 'no'\n"
            "    # args.mixed_precision is a new argument which needs to be set now\n"
            "\n"
        )
        extra_args += mixed_precision

    # Check if per_device_eval_batch_size (default 8) bigger than bsz
    # Also use FP16 / BF16 evaluation
    if "args" in call_args:
        # Check eval_dataset first
        if "eval_dataset" in call_args:
            check_eval_dataset = (
                "if getattr(args, 'eval_dataset', None) is not None and "
                "getattr(args, 'eval_strategy', 'no') == 'no':\n"
                "    args.eval_strategy = 'steps'\n"
                "    if getattr(args, 'eval_steps', None) is None: args.eval_steps = 0.1\n"
            )
            extra_args += check_eval_dataset

        # Check if gradient accumulation bug fix is applied
        check_ga = (
            "ga_steps = getattr(args, 'gradient_accumulation_steps', None)\n"
            "if ga_steps is not None and ga_steps > 1:\n"
            "    from transformers import __version__ as transformers_version\n"
            "    if Version(transformers_version) <= Version('4.45.2'):\n"
            "        print('**** Unsloth: Please use our fixed gradient_accumulation_steps by updating transformers, TRL and Unsloth!\\n'\n"
            "              '`pip install --upgrade --no-cache-dir --force-reinstall --no-deps unsloth transformers trl unsloth_zoo`')\n"
        )
        extra_args += check_ga

        eval_changes = (
            "if getattr(args, 'eval_strategy', 'no') != 'no':\n"
            "    eval_bsz = getattr(args, 'per_device_eval_batch_size', 8)\n"
            "    if eval_bsz == 8 and args.per_device_train_batch_size < eval_bsz: args.per_device_eval_batch_size = args.per_device_train_batch_size\n"
            "    if getattr(args, 'eval_accumulation_steps', None) is None and ga_steps is not None: args.eval_accumulation_steps = ga_steps\n"
            "fp16_full_eval = getattr(args, 'fp16_full_eval', False)\n"
            "if type(fp16_full_eval) is not bool: fp16_full_eval = False\n"
            "bf16_full_eval = getattr(args, 'bf16_full_eval', False)\n"
            "if type(bf16_full_eval) is not bool: bf16_full_eval = False\n"
            "if args.fp16 and bf16_full_eval: args.bf16_full_eval = False; args.fp16_full_eval = True\n"
            "if args.bf16 and fp16_full_eval: args.bf16_full_eval = True; args.fp16_full_eval = False\n"
            "if force_float32:\n"
            "    args.bf16_full_eval = False\n"
            "    args.fp16_full_eval = False\n"
            "elif os.environ.get('UNSLOTH_MIXED_PRECISION', 'float32') == 'bfloat16':\n"
            "    args.bf16_full_eval = True\n"
            "    args.fp16_full_eval = False\n"
            "elif not bf16_full_eval and not fp16_full_eval:\n"
            "    args.bf16_full_eval = args.bf16\n"
            "    args.fp16_full_eval = args.fp16\n"
        )
        extra_args += eval_changes

    # Force logits to be produced if preprocess_logits_for_metrics or compute_metrics is used
    if "model" in call_args:
        logits_check = (
            "_output_logits = False\n"
            "if locals().get('compute_metrics', None) is not None: _output_logits = True\n"
            "if locals().get('preprocess_logits_for_metrics', None) is not None: _output_logits = True\n"
            "if _output_logits:\n"
            "    os.environ['UNSLOTH_RETURN_LOGITS'] = '1'\n"
        )
        extra_args += logits_check
        warnings_issued_check = (
            "if model is not None:\n"
            "    _warnings_issued = getattr(model, 'warnings_issued', None)\n"
            "    if _warnings_issued is None:\n"
            "        model.warnings_issued = {}\n"
            "    elif not isinstance(_warnings_issued, dict):\n"
            "        try:\n"
            "            model.warnings_issued = dict(_warnings_issued)\n"
            "        except Exception:\n"
            "            model.warnings_issued = {}\n"
        )
        extra_args += warnings_issued_check

    # Check max_seq_length
    if "model" in call_args:
        length_check = (
            "if 'max_seq_length' not in locals() and not hasattr(args, 'max_seq_length'):\n"
            "    pass\n"
            "else:\n"
            "    model_max_seq_length = getattr(model, 'max_seq_length', None)\n"
            "    args_max_seq_length  = getattr(args,  'max_seq_length', None)\n"
            "    if args_max_seq_length is None and model_max_seq_length is not None:\n"
            "        max_seq_length = model.max_seq_length\n"
            "        if hasattr(args, 'max_seq_length'): args.max_seq_length = max_seq_length\n"
            "    elif args_max_seq_length is not None and model_max_seq_length is not None:\n"
            "        if args_max_seq_length > model_max_seq_length:\n"
            "            print('Unsloth: You set `max_seq_length` as ' + str(args_max_seq_length) + ' but '\n"
            "                   'the maximum the model supports is ' + str(model_max_seq_length) + '. We shall reduce it.')\n"
            "            args.max_seq_length = model_max_seq_length\n"
        )
        extra_args += length_check

        # At this point max_seq_length might be set, but trl is moving to max_length
        if trainer_file == "sft_trainer":
            max_length_check = (
                "if 'max_length' not in locals() and not hasattr(args, 'max_length'):\n"
                "    pass\n"
                "else:\n"
                "    if hasattr(args, 'max_seq_length') and args.max_seq_length is not None and args.max_seq_length > 0:\n"
                "        if hasattr(args, 'max_length'):\n"
                "            args.max_length = args.max_seq_length\n"
                "            max_length = args.max_length\n"
                "    else:\n"
                "        model_max_length = getattr(model, 'max_seq_length', None)\n"
                "        if model_max_length is None: model_max_length = getattr(model, 'max_length', None)\n"
                "        if model_max_length is not None:\n"
                "            args.max_length = model_max_length\n"
                "            max_length = args.max_length\n"
                "        elif hasattr(args, 'max_length') and args.max_length is not None:\n"
                "            max_length = args.max_length\n"
                "            # if we are here, then we are in a weird case where max_length is set but max_seq_length is not set\n"
                "            setattr(model, 'max_seq_length', max_length)\n"
                "        else:\n"
                "            print('Unsloth: We did not find `max_seq_length` or `max_length` in the model or args. We will set it to 1024.')\n"
                "            args.max_length = 1024\n"
            )
            extra_args += max_length_check

    # Enable for training and move padding side of tokenizer to right
    if "model" in call_args:
        training_check = (
            "if model is not None and hasattr(model, 'for_training'):\n"
            "    model.for_training(use_gradient_checkpointing=getattr(args, 'gradient_checkpointing', True))\n"
            "if 'tokenizer' in locals() and hasattr(tokenizer, 'padding_side'): tokenizer.padding_side = 'right'\n"
            "if 'processing_class' in locals():\n"
            "    if hasattr(processing_class, 'padding_side'): processing_class.padding_side = 'right'\n"
            "    if hasattr(processing_class, 'tokenizer') and hasattr(processing_class.tokenizer, 'padding_side'): "
            "processing_class.tokenizer.padding_side = 'right'\n"
        )
        extra_args += training_check

    # Check data collator if it's correct!
    if "data_collator" in call_args and "train_dataset" in call_args:
        data_collator_check = (
            "__tokenizer = processing_class if 'processing_class' in locals() else tokenizer\n"
            "from unsloth_zoo.vision_utils import UnslothVisionDataCollator\n"
            "if not isinstance(data_collator, UnslothVisionDataCollator):\n"
            "    if isinstance(data_collator, DataCollatorForSeq2Seq) and 'labels' not in train_dataset.column_names:\n"
            "        data_collator = TransformersDataCollatorForLanguageModeling(\n"
            "            __tokenizer,\n"
            "            mlm = False,\n"
            "            mlm_probability = 0.0,\n"
            "            pad_to_multiple_of = getattr(args, 'pad_to_multiple_of', None),\n"
            "        )\n"
            "    elif isinstance(data_collator, TransformersDataCollatorForLanguageModeling) and 'labels' in train_dataset.column_names:\n"
            "        data_collator = DataCollatorForSeq2Seq(\n"
            "            __tokenizer,\n"
            "            pad_to_multiple_of = getattr(args, 'pad_to_multiple_of', None),\n"
            "        )\n"
            "else:\n"
            "    if hasattr(args, 'remove_unused_columns'): args.remove_unused_columns = False\n"
            "    if hasattr(args, 'dataset_text_field'): args.dataset_text_field = ''\n"
            "    if hasattr(args, 'dataset_kwargs'): args.dataset_kwargs = {'skip_prepare_dataset': True}\n"
        )
        extra_args += data_collator_check

        # Also check if .pad exists -> if not, and is VLM, then change it!
        pad_check = (
            "if not isinstance(data_collator, UnslothVisionDataCollator):\n"
            "    if not hasattr(__tokenizer, 'pad') and hasattr(__tokenizer, 'tokenizer'):\n"
            "        if isinstance(data_collator, DataCollatorForSeq2Seq):\n"
            "            data_collator = DataCollatorForSeq2Seq(\n"
            "                __tokenizer.tokenizer,\n"
            "                pad_to_multiple_of = getattr(args, 'pad_to_multiple_of', None),\n"
            "            )\n"
            "        else:\n"
            "            data_collator = TransformersDataCollatorForLanguageModeling(\n"
            "                __tokenizer.tokenizer,\n"
            "                mlm = False,\n"
            "                mlm_probability = 0.0,\n"
            "                pad_to_multiple_of = getattr(args, 'pad_to_multiple_of', None),\n"
            "            )\n"
        )
        extra_args += pad_check

    # Check NEFTune
    if "model" in call_args:
        neftune_check = (
            "if hasattr(self, 'neftune_hook_handle'):\n"
            "    self.neftune_hook_handle.remove()\n"
            "    if hasattr(self, 'neftune_hook_handle'): del self.neftune_hook_handle\n"
            "if getattr(args, 'neftune_noise_alpha', None) is not None:\n"
            "    model.get_input_embeddings().neftune_noise_alpha = self.neftune_noise_alpha\n"
            "pass\n"
        )
        RLTrainer_post += neftune_check

    # Add accelerator scaler to model
    if "model" in call_args:
        accelerator_check = (
            "if hasattr(self, 'accelerator'):\n"
            "    scaler = self.accelerator.scaler\n"
            "    current_model = model\n"
            "    while hasattr(current_model, 'model'):\n"
            "        current_model.accelerator_scaler = scaler\n"
            "        current_model = current_model.model\n"
            "    current_model.accelerator_scaler = scaler\n"
            "pass\n"
        )
        RLTrainer_post += accelerator_check

    # Add enabling and disabling training modes
    if "model" in call_args:
        training_check = (
            "if hasattr(self, 'train'):\n"
            "    self.train = MethodType(prepare_for_training_mode(self.__class__.train), self)\n"
            "pass\n"
        )
        RLTrainer_post += training_check

    # Sync chat_template from processing_class to vLLM's tokenizer
    # This fixes base models that have custom chat templates applied after loading
    if "model" in call_args:
        vllm_chat_template_sync = (
            "if hasattr(self, 'llm') and self.llm is not None and hasattr(self.llm, 'get_tokenizer'):\n"
            "    _vllm_tok = self.llm.get_tokenizer()\n"
            "    _pc = getattr(self, 'processing_class', None) or getattr(self, 'tokenizer', None)\n"
            "    if _vllm_tok is not None and _pc is not None and getattr(_pc, 'chat_template', None) is not None and getattr(_vllm_tok, 'chat_template', None) is None:\n"
            "        _vllm_tok.chat_template = _pc.chat_template\n"
            "pass\n"
        )
        RLTrainer_post += vllm_chat_template_sync

    # Edit optional metrics
    other_metrics_processor = ""
    if trainer_file in RL_METRICS_CHANGES:
        process_extra_args = RL_METRICS_CHANGES[trainer_file]
        for process_extra_arg in process_extra_args:
            other_metrics_processor += process_extra_arg(
                old_RLTrainer_source, old_RLConfig_source
            )

    # Add statistics as well!
    extra_args += (
        "other_metrics = []\n"
        f"{other_metrics_processor}\n"
        "from unsloth_zoo.logging_utils import PatchRLStatistics\n"
        f"PatchRLStatistics('{trainer_file}', other_metrics)\n"
    )

    # Patch optional args
    if trainer_file in RL_EXTRA_ARGS:
        process_extra_args = RL_EXTRA_ARGS[trainer_file]
        for process_extra_arg in process_extra_args:
            extra_args += process_extra_arg(call_args, extra_args)

    # Create RLTrainer args
    extra_args = extra_args.split("\n")
    extra_args = "\n".join(" " * 8 + x for x in extra_args)
    RLTrainer_post = RLTrainer_post.split("\n")
    RLTrainer_post = "\n".join(" " * 8 + x for x in RLTrainer_post)
    RLTrainer_arguments = arguments
    RLTrainer_extra_args = extra_args
    RLTrainer_call_args = call_args

    # Fix RLConfig next
    arguments, call_args = processed[1]
    extra_args = ""

    # Edit GA / bsz and weight_decay
    replacements = {
        "output_dir": None,
        "logging_nan_inf_filter": False,
        "per_device_train_batch_size": 4,
        "gradient_accumulation_steps": 2,
        "weight_decay": 0.01,
        "seed": 3407,
        "optim": "adamw_8bit",
        "learning_rate": 5e-05,
        "per_device_eval_batch_size": 4,
        "eval_accumulation_steps": 2,
        "torch_empty_cache_steps": 250,
        "logging_steps": 1,
        "max_seq_length": None,
        "num_generations": 8,
        # "steps_per_generation"          : 1, # Otherwise defaults to ga_steps which is wrong
        # "generation_batch_size"         : None, # Useless. If steps_per_generation set, generation_batch_size clashes
        "top_k": None,
        "vllm_mode": "colocate",
        "generation_kwargs": {},
        "bf16": False,
        "fp16": False,
        "report_to": "none",
        "include_tokens_per_second": False,
        "include_num_input_tokens_seen": False,
        "auto_find_batch_size": False,  # Auto /2 batch size - too many people complained so removing
        "dataloader_pin_memory": True,
        "padding_free": None,  # None = user didn't set it, allows auto-enable detection
        # Might fail so disable for now
        # "dataloader_persistent_workers" : True, # Keeps dataloader in RAM
        # "dataloader_prefetch_factor"    : 2,
        # "dataloader_num_workers"        : 2, # Default is 0 means 1
    }
    # warmup_ratio deprecated in transformers >= 5.0; warmup_steps accepts float
    if transformers_version >= Version("5.0.0"):
        replacements["warmup_steps"] = 0.1
    else:
        replacements["warmup_ratio"] = 0.1

    for k, v in replacements.items():
        x = f"{k}( = [^,\n]{{1,}})?,\n"
        y = f"'{v}'" if type(v) is str else f"{v}"
        y = f"{k} = {y},\n"
        arguments = re.sub(x, y, arguments)

    # Fix GRPO beta default as 0.001 TRL used to be 0.04, now 0.00!
    # https://github.com/huggingface/trl/pull/3516
    # https://verl.readthedocs.io/en/latest/examples/config.html
    if trainer_file == "grpo_trainer":
        replacements = {
            "loss_type": "bnpo",  # Default GRPO paper
            "beta": 0.001,  # Recommended as seen in verl
            "auto_find_batch_size": False,  # Cannot work on GRPO
            # [TODO] See https://fengyao.notion.site/off-policy-rl
            # https://github.com/huggingface/trl/pull/3867 (August 7th)
            "vllm_importance_sampling_correction": False,
        }
        for k, v in replacements.items():
            x = f"{k}( = [^,\n]{{1,}})?,\n"
            y = f"'{v}'" if type(v) is str else f"{v}"
            y = f"{k} = {y},\n"
            arguments = re.sub(x, y, arguments)

    # Warn on too large or too small learning rate
    if "learning_rate" in call_args:
        learning_rate_check = (
            "if learning_rate < 1e-7: print(f'Unsloth: Your learning rate of `{learning_rate}` is too small and less than 1e-7! "
            "Consider increasing it, otherwise gradient updates will be close to 0!')\n"
            "if learning_rate > 1: print(f'Unsloth: Your learning rate of `{learning_rate}` is way too larger > 1! "
            "Consider decreasing it to 1e-1, otherwise gradient updates will explode!')\n"
        )
        extra_args += learning_rate_check

    # Fix num_train_epochs = None causing TypeError in Trainer.__init__
    # Trainer does `args.num_train_epochs > 0` which fails when None
    if "num_train_epochs" in call_args:
        num_train_epochs_check = (
            "if num_train_epochs is None:\n"
            "    num_train_epochs = 3.0  # Default to 3 epochs if None, max_steps will override\n"
        )
        extra_args += num_train_epochs_check

    # Check if max_seq_length is NOT defined (max_length is now default)
    if "max_seq_length" not in call_args and "max_length" in call_args:
        max_seq_length_pre = """max_seq_length : Optional[int] = field(
        default = None,
        metadata = {'help': 'Maximum sequence length to truncate to.'},
    )"""
        max_seq_length_call = "max_seq_length = None,"
        max_seq_length_post = "self.max_seq_length = max_seq_length"
    else:
        max_seq_length_pre = ""
        max_seq_length_call = ""
        max_seq_length_post = ""

    # Add output_dir saving
    if "output_dir" in call_args:
        # Default checks
        saving_check = (
            "if output_dir is None and save_strategy == 'steps' and save_steps == 500:\n"
            "    output_dir = 'unsloth_training_checkpoints'\n"
            "    save_strategy = 'no'\n"
        )
        extra_args += saving_check

    # Edit dataset_num_proc
    if "dataset_num_proc" in call_args:
        num_proc_check = (
            "import multiprocessing as _mp\n"
            "if dataset_num_proc is None:\n"
            "    if _mp.get_start_method() != 'fork':\n"
            "        dataset_num_proc = None\n"
            "    else:\n"
            "        import psutil\n"
            "        dataset_num_proc = min(max((psutil.cpu_count() or 1)+4, 2), 64)\n"
            "        memory_gb_left = psutil.virtual_memory().available / (1024**3)\n"
            "        if memory_gb_left <= 2: dataset_num_proc = 1\n"
            "        else: dataset_num_proc = min(dataset_num_proc, int(memory_gb_left))\n"
        )
        extra_args += num_proc_check

    # Add padding if flex attention is added
    if "pad_to_multiple_of" in call_args:
        pad_to_multiple_of = (
            "if os.environ.get('UNSLOTH_ENABLE_FLEX_ATTENTION', '0') == '1':\n"
            "    from unsloth_zoo.flex_attention import HAS_FLEX_ATTENTION\n"
            "    if HAS_FLEX_ATTENTION and pad_to_multiple_of is None:\n"
            "        from unsloth_zoo.flex_attention import FLEX_ATTENTION_BLOCK_SIZE\n"
            "        pad_to_multiple_of = FLEX_ATTENTION_BLOCK_SIZE\n"
            "\n"
        )
        extra_args += pad_to_multiple_of

    # Check for loss_type = dr_grpo and scale_rewards for GRPO
    if "loss_type" in call_args and "scale_rewards" in call_args:
        # See https://github.com/huggingface/trl/issues/3130#issuecomment-2746947835
        # DAPO uses per token loss so BNPO loss used
        check_dr_grpo = (
            "if loss_type.lower() == 'dr_grpo':\n"
            "    loss_type = 'dr_grpo'\n"
            "elif loss_type.lower() == 'dapo':\n"
            "    loss_type = 'dapo'\n"
            "if loss_type.lower() == 'dr_grpo':\n"
            "    if scale_rewards == None:\n"
            "        scale_rewards = True\n"
            "    elif scale_rewards == True:\n"
            "        print('Unsloth: The Dr GRPO paper recommends setting `scale_rewards` to False! Will override. Set it to `None` to force False.')\n"
            "        scale_rewards = False\n"
            "elif loss_type.lower() == 'dapo':\n"
            "    if mask_truncated_completions != True:\n"
            "        print('Unsloth: The DAPO paper recommends `mask_truncated_completions = True` - we will set it.')\n"
            "    if epsilon_high != 0.28:\n"
            "        print('Unsloth: The DAPO paper recommends `epsilon_high = 0.28` - we will set it.')\n"
            "    if beta != 0.0:\n"
            "        print(f'[WARNING] Unsloth: The DAPO paper recommends setting `beta = 0.0` to remove the KL term - You have set it to {beta}.')\n"
            "    mask_truncated_completions = True\n"
            "    epsilon_high = 0.28\n"
            "\n"
        )
        extra_args += check_dr_grpo

    # Check GRPO num_generations mismatch
    if (
        "per_device_train_batch_size" in call_args
        and "num_generations" in call_args
        and "steps_per_generation" in call_args
        and "generation_batch_size" in call_args
    ):
        # if world size is not set by accelerate or torchrun at this point it will be 1
        check_num_generations = (
            "if steps_per_generation is None and generation_batch_size is None:\n"
            "    ga = gradient_accumulation_steps\n"
            "    world_size = int(os.environ.get('WORLD_SIZE', '1'))\n"
            "    if (ga * world_size * per_device_train_batch_size) % num_generations != 0:\n"
            "        print('Unsloth: We now expect `per_device_train_batch_size` * `gradient_accumulation_steps` * `world_size` to be a multiple of `num_generations`.\\n"
            "We will change the batch size of ' + str(per_device_train_batch_size) + ' to the `num_generations` of ' + str(num_generations))\n"
            "        per_device_train_batch_size = num_generations\n"
            "\n"
        )
        extra_args += check_num_generations
    elif "per_device_train_batch_size" in call_args and "num_generations" in call_args:
        if "steps_per_generation" not in call_args:
            print(f"Unsloth: Could not find `steps_per_generation` in {trainer_file}")
        if "generation_batch_size" not in call_args:
            print(f"Unsloth: Could not find `generation_batch_size` in {trainer_file}")

        check_num_generations = (
            "if (per_device_train_batch_size // num_generations) * num_generations != per_device_train_batch_size:\n"
            "    print('Unsloth: We now expect `per_device_train_batch_size` to be a multiple of `num_generations`.\\n"
            "We will change the batch size of ' + str(per_device_train_batch_size) + ' to the `num_generations` of ' + str(num_generations))\n"
            "    per_device_train_batch_size = num_generations\n"
            "\n"
        )
        extra_args += check_num_generations

    # Check temperature must not be <= 0. Also stop if >= 10
    if "temperature" in call_args:
        check_temperature = (
            "if temperature <= 0:\n"
            "    raise ValueError('Unsloth: Please set a positive non-zero temperature since your results will be wrong.')\n"
            "elif temperature >= 10:\n"
            "    raise ValueError('Unsloth: Please set a positive non-zero temperature less than 10, since sampling will be quite erratic.')\n"
            "\n"
        )
        extra_args += check_temperature

    # Edit config with anything extra
    if trainer_file in RL_CONFIG_CHANGES:
        process_extra_args = RL_CONFIG_CHANGES[trainer_file]
        for process_extra_arg in process_extra_args:
            extra_args += process_extra_arg(old_RLTrainer_source, old_RLConfig_source)

    # Create RLConfig args
    extra_args = extra_args.split("\n")
    extra_args = "\n".join(" " * 8 + x for x in extra_args)
    RLConfig_arguments = arguments
    RLConfig_extra_args = extra_args
    RLConfig_call_args = call_args

    # TRL 0.27.0+ forces use_reentrant=False in gradient_checkpointing_kwargs.
    # Unsloth gradient checkpointing requires use_reentrant=True, so we remove
    # the setting after super().__init__() when it gets auto-applied.
    RLConfig_post = ""
    if trl_version >= Version("0.27.0"):
        RLConfig_post = (
            "        # Unsloth: Remove use_reentrant=False forced by TRL 0.27.0+\n"
            "        if getattr(self, 'gradient_checkpointing_kwargs', None) is not None:\n"
            "            if 'use_reentrant' in self.gradient_checkpointing_kwargs:\n"
            "                del self.gradient_checkpointing_kwargs['use_reentrant']\n"
        )

    # Patch vLLM and other functions
    RLTrainer_extras = patch_functions(
        RLTrainer, trainer_file, RLTrainer_name, all_imports, imports
    )
    if RLTrainer_extras is None:
        RLTrainer_extras = f"_Unsloth{RLTrainer_name} = {RLTrainer_name}"

    # Create full module
    exec(f"from trl.trainer import ({RLTrainer_name}, {RLConfig_name},)")
    __RLTrainer_doc__ = eval(f"trl.trainer.{RLTrainer_name}").__doc__
    if __RLTrainer_doc__ is None:
        __RLTrainer_doc__ = ""
    __RLConfig_doc__ = eval(f"trl.trainer.{RLConfig_name}").__doc__
    if __RLConfig_doc__ is None:
        __RLConfig_doc__ = ""

    # Get all pre-modules
    if trainer_file in RL_PRE_ITEMS:
        RL_pre = "\n".join(RL_PRE_ITEMS[trainer_file])
    else:
        RL_pre = ""

    # Check if SamplingParams is in there
    if "SamplingParams" in old_RLTrainer_source:
        RL_pre = RL_pre + "\n" + inspect.getsource(vLLMSamplingParams)

    # Selective log softmax and other functions
    selective_log_softmax_code = inspect.getsource(selective_log_softmax)
    grpo_selective_log_softmax_code = inspect.getsource(grpo_selective_log_softmax)
    calculate_pad_tokens_in_prompt_code = inspect.getsource(
        calculate_pad_tokens_in_prompt
    )
    create_completion_attention_mask_code = inspect.getsource(
        create_completion_attention_mask
    )
    left_pack_padding_code = inspect.getsource(left_pack_padding)
    align_logprobs_with_mask_code = inspect.getsource(align_logprobs_with_mask)
    autotune_batch_and_chunks_code = inspect.getsource(autotune_batch_and_chunks)
    sanitize_logprob_code = inspect.getsource(sanitize_logprob)
    # Get final source code
    RLTrainer_source = RLTrainer_replacement.format(
        RLTrainer_name = RLTrainer_name,
        __RLTrainer_doc__ = __RLTrainer_doc__,
        RLTrainer_arguments = RLTrainer_arguments,
        RLTrainer_extra_args = RLTrainer_extra_args,
        RLTrainer_call_args = RLTrainer_call_args,
        RLTrainer_kwargs = ",**kwargs"[1 if RLTrainer_call_args.endswith(",") else 0 :],
        RLConfig_name = RLConfig_name,
        __RLConfig_doc__ = __RLConfig_doc__,
        RLConfig_arguments = RLConfig_arguments,
        RLConfig_extra_args = RLConfig_extra_args,
        RLConfig_call_args = RLConfig_call_args,
        RLConfig_kwargs = ",**kwargs"[1 if RLConfig_call_args.endswith(",") else 0 :],
        RLConfig_post = RLConfig_post,
        RLTrainer_extras = RLTrainer_extras,
        RLTrainer_post = RLTrainer_post,
        RL_pre = RL_pre,
        max_seq_length_pre = max_seq_length_pre,
        max_seq_length_call = max_seq_length_call,
        max_seq_length_post = max_seq_length_post,
        selective_log_softmax_code = selective_log_softmax_code,
        grpo_selective_log_softmax_code = grpo_selective_log_softmax_code,
        calculate_pad_tokens_in_prompt_code = calculate_pad_tokens_in_prompt_code,
        create_completion_attention_mask_code = create_completion_attention_mask_code,
        autotune_batch_and_chunks_code = autotune_batch_and_chunks_code,
        left_pack_padding_code = left_pack_padding_code,
        align_logprobs_with_mask_code = align_logprobs_with_mask_code,
        sanitize_logprob_code = sanitize_logprob_code,
    )

    if RLTrainer_name == "GRPOTrainer":
        # Base torch_compile_options shared by all device types
        base_options = """torch_compile_options = {
            "epilogue_fusion"   : True,
            "max_autotune"      : False,
            "shape_padding"     : True,
            "trace.enabled"     : False,"""

        # Generate torch_compile_options based on device type
        if DEVICE_TYPE == "cuda":
            # CUDA-specific options (added to base options)
            cuda_options = """
            "triton.enable_persistent_tma_matmul": torch.cuda.get_device_capability()[0] >= 9,"""
            # cutlass options were added in PyTorch 2.8.0
            if torch_version >= Version("2.8.0"):
                cuda_options += """
            "cuda.cutlass_epilogue_fusion_enabled": torch.cuda.get_device_capability()[0] >= 9,
            "cuda.cutlass_tma_only": torch.cuda.get_device_capability()[0] >= 9,"""
            cuda_options += """
            "cuda.compile_opt_level"              : "-O2",
            "cuda.enable_cuda_lto"                : True,
        }"""
            new_options = base_options + cuda_options
        else:
            # XPU, HIP, and other device types use base options only
            new_options = (
                base_options
                + """
        }"""
            )

        pattern = r"torch_compile_options\s*=\s*\{[^}]*\}"

        RLTrainer_source = re.sub(
            pattern, new_options, RLTrainer_source, flags = re.DOTALL
        )

        if trl_version >= Version("0.27.0"):
            peft_pattern = (
                r"\s*if is_peft_available\(\) and is_peft_model\(model\) and args\.beta != 0\.0:"
                r".*?"
                r"param\.data = param\.data\.to\(torch\.bfloat16\)"
            )

            replacement_comment = "\n        # PEFT initialization logic removed via script for trl >= 0.27.0\n"

            RLTrainer_source = re.sub(
                peft_pattern, replacement_comment, RLTrainer_source, flags = re.DOTALL
            )

        elif trl_version >= Version("0.26.0"):
            peft_block_pattern = (
                r"\s*if is_peft_available\(\) and isinstance\(model, PeftModel\) and peft_config is not None:"
                r".*?"
                r"param\.data = param\.data\.to\(torch\.bfloat16\)"
            )

            RLTrainer_source = re.sub(
                peft_block_pattern,
                "\n        # TRL PEFT 0.26.0 initialization logic removed on unsloth side.\n",
                RLTrainer_source,
                flags = re.DOTALL,
            )

    # Remove TRL's unconditional bfloat16 cast of trainable params (added in
    # TRL 0.26.0). TRL hardcodes bfloat16 for QLoRA per the original paper's
    # recommendation, but this is wrong: it ignores the user's requested dtype
    # and breaks GradScaler when training with fp16=True. Unsloth already
    # handles adapter dtype correctly via patch_model_and_tokenizer, so the
    # entire block is unnecessary. For GRPOTrainer the enclosing peft init
    # block is already removed above, making this a no-op for GRPO.
    RLTrainer_source = RLTrainer_source.replace(
        'if getattr(model, "is_loaded_in_4bit", False) or getattr(model, "is_loaded_in_8bit", False):',
        "if False:",
    )

    if RLTrainer_name == "SFTTrainer":
        original_text = 'self._signature_columns = ["input_ids", "attention_mask", "completion_mask"]'
        new_text = 'self._signature_columns = ["input_ids", "attention_mask", "completion_mask","labels"]'
        RLTrainer_source = RLTrainer_source.replace(original_text, new_text)

        # Do NOT override _is_vlm -- let TRL detect VLM models naturally.
        # In TRL 0.27.1+, forcing _is_vlm=False causes a ValueError when
        # vision datasets are used with VLM models.
        #
        # However, some notebooks pass a bare tokenizer (processor.tokenizer) as
        # processing_class. TRL then sets _is_vlm=False even for VLM models.
        # Add a model-architecture-based override before the validation check.
        _vlm_check_original = (
            '        self._is_vision_dataset = "image" in dataset_sample or "images" in dataset_sample\n'
            "        if self._is_vision_dataset and not self._is_vlm:"
        )
        _vlm_check_patched = (
            '        self._is_vision_dataset = "image" in dataset_sample or "images" in dataset_sample\n'
            "        # Unsloth: override _is_vlm for VLM models that pass a bare tokenizer\n"
            "        if not self._is_vlm and self._is_vision_dataset:\n"
            "            _m = model\n"
            '            if hasattr(_m, "model"): _m = _m.model\n'
            '            if hasattr(getattr(_m, "config", None), "vision_config") or \\\n'
            '               _m.__class__.__name__.endswith("ForConditionalGeneration"):\n'
            "                self._is_vlm = True\n"
            "        if self._is_vision_dataset and not self._is_vlm:"
        )
        if _vlm_check_original in RLTrainer_source:
            RLTrainer_source = RLTrainer_source.replace(
                _vlm_check_original, _vlm_check_patched
            )

        # Fix TRL 0.22.x: VLM models with text-only datasets.
        # TRL 0.22.x checks _is_vlm (model type) not _is_vision_dataset (dataset
        # content, added in 0.25.1+). When _is_vlm=True, signature columns are
        # vision-only ["messages","prompt","completion","images"], which have zero
        # overlap with tokenized text columns. Fix: merge both column sets into the
        # VLM branch. Extra columns not in the dataset are harmlessly ignored by
        # _remove_unused_columns (it only raises when zero columns match).
        _sig_vlm_old = (
            'self._signature_columns = ["messages", "prompt", "completion", "images"]'
        )
        _sig_vlm_new = (
            'self._signature_columns = ["messages", "prompt", "completion", "images",'
            ' "input_ids", "labels", "attention_mask", "seq_lengths", "completion_mask", "assistant_masks"]'
        )
        RLTrainer_source = RLTrainer_source.replace(_sig_vlm_old, _sig_vlm_new)

        # Inject model reference before _prepare_dataset for dynamic
        # token_type_ids detection in sft_prepare_dataset
        _prep_pattern = r"([ \t]*)train_dataset = self\._prepare_dataset\("
        _prep_replacement = r"\1self._unsloth_model_ref = model\n\1train_dataset = self._prepare_dataset("
        RLTrainer_source = re.sub(
            _prep_pattern, _prep_replacement, RLTrainer_source, count = 1
        )

    # Silence TRL's noisy batch_size=1 + padding-free warning (handles both
    # the original "anihilate" typo and the corrected "annihilate" spelling)
    for _typo in ("anihilate", "annihilate"):
        _idx = RLTrainer_source.find(_typo)
        if _idx == -1:
            continue
        # Walk backwards to find "if args.per_device_train_batch_size"
        _block_start = RLTrainer_source.rfind(
            "if args.per_device_train_batch_size == 1", 0, _idx
        )
        if _block_start == -1:
            continue
        # Walk backwards to the newline before the if
        _line_start = RLTrainer_source.rfind("\n", 0, _block_start)
        # Walk forwards past the closing paren to the end of the block
        _close = RLTrainer_source.find(")", _idx)
        if _close == -1:
            continue
        _block_end = RLTrainer_source.find("\n", _close)
        if _block_end == -1:
            continue
        RLTrainer_source = (
            RLTrainer_source[:_line_start] + RLTrainer_source[_block_end:]
        )
        break

    # Remove multiple doc strings
    if __RLConfig_doc__ != "" and RLTrainer_source.count(__RLTrainer_doc__) == 2:
        RLTrainer_source = RLTrainer_source.replace(__RLTrainer_doc__, "", 1)

    # Remove multiple newlines
    RLTrainer_source = re.sub(r"[\n]{3,}", "\n", RLTrainer_source)

    # Create new function
    _resolved_module = _trainer_resolved_module or _config_resolved_module
    _model_location = (
        _resolved_module.__name__
        if _resolved_module is not None
        else f"trl.trainer.{trainer_file}"
    )
    created_module = create_new_function(
        f"Unsloth{RLTrainer_name}",
        RLTrainer_source,
        _model_location,
        imports,
        overwrite = False,
    )
    patched_trainer = getattr(created_module, f"Unsloth{RLTrainer_name}")
    if trainer_file == "grpo_trainer":
        _patch_resume_from_checkpoint_memory(patched_trainer)

    # Patch Trainer
    exec(
        f"trl.{RLTrainer_name} = created_module.Unsloth{RLTrainer_name}",
        locals(),
        globals(),
    )
    exec(
        f"trl.trainer.{RLTrainer_name} = created_module.Unsloth{RLTrainer_name}",
        locals(),
        globals(),
    )
    exec(
        f"trl.trainer.{trainer_file}.{RLTrainer_name} = created_module.Unsloth{RLTrainer_name}",
        locals(),
        globals(),
    )

    # Patch Config
    exec(
        f"trl.{RLConfig_name} = created_module.Unsloth{RLConfig_name}",
        locals(),
        globals(),
    )
    exec(
        f"trl.trainer.{RLConfig_name} = created_module.Unsloth{RLConfig_name}",
        locals(),
        globals(),
    )
    exec(
        f"trl.trainer.{trainer_file}.{RLConfig_name} = created_module.Unsloth{RLConfig_name}",
        locals(),
        globals(),
    )

    if trainer_file == "grpo_trainer":
        try:
            _wrap_grpo_generate_and_score(
                getattr(created_module, f"Unsloth{RLTrainer_name}")
            )
        except Exception as e:
            logger.info(
                f"Unsloth: Could not wrap _generate_and_score_completions for {RLTrainer_name}: {e}"
            )