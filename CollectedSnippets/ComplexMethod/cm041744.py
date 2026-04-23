def _parse_train_args(self, data: dict["Component", Any]) -> dict[str, Any]:
        r"""Build and validate the training arguments."""
        get = lambda elem_id: data[self.manager.get_elem_by_id(elem_id)]
        model_name, finetuning_type = get("top.model_name"), get("top.finetuning_type")
        user_config = load_config()

        args = dict(
            stage=TRAINING_STAGES[get("train.training_stage")],
            do_train=True,
            model_name_or_path=get("top.model_path"),
            cache_dir=user_config.get("cache_dir", None),
            preprocessing_num_workers=16,
            finetuning_type=finetuning_type,
            template=get("top.template"),
            rope_scaling=get("top.rope_scaling") if get("top.rope_scaling") != "none" else None,
            flash_attn="fa2" if get("top.booster") == "flashattn2" else "auto",
            use_unsloth=(get("top.booster") == "unsloth"),
            enable_liger_kernel=(get("top.booster") == "liger_kernel"),
            dataset_dir=get("train.dataset_dir"),
            dataset=",".join(get("train.dataset")),
            cutoff_len=get("train.cutoff_len"),
            learning_rate=float(get("train.learning_rate")),
            num_train_epochs=float(get("train.num_train_epochs")),
            max_samples=int(get("train.max_samples")),
            per_device_train_batch_size=get("train.batch_size"),
            gradient_accumulation_steps=get("train.gradient_accumulation_steps"),
            lr_scheduler_type=get("train.lr_scheduler_type"),
            max_grad_norm=float(get("train.max_grad_norm")),
            logging_steps=get("train.logging_steps"),
            save_steps=get("train.save_steps"),
            warmup_steps=get("train.warmup_steps"),
            neftune_noise_alpha=get("train.neftune_alpha") or None,
            packing=get("train.packing") or get("train.neat_packing"),
            neat_packing=get("train.neat_packing"),
            train_on_prompt=get("train.train_on_prompt"),
            mask_history=get("train.mask_history"),
            resize_vocab=get("train.resize_vocab"),
            use_llama_pro=get("train.use_llama_pro"),
            enable_thinking=get("train.enable_thinking"),
            report_to=get("train.report_to"),
            use_galore=get("train.use_galore"),
            use_apollo=get("train.use_apollo"),
            use_badam=get("train.use_badam"),
            use_swanlab=get("train.use_swanlab"),
            output_dir=get_save_dir(model_name, finetuning_type, get("train.output_dir")),
            fp16=(get("train.compute_type") == "fp16"),
            bf16=(get("train.compute_type") == "bf16"),
            pure_bf16=(get("train.compute_type") == "pure_bf16"),
            plot_loss=True,
            trust_remote_code=True,
            ddp_timeout=180000000,
            include_num_input_tokens_seen=True,
        )
        args.update(json.loads(get("train.extra_args")))

        # checkpoints
        if get("top.checkpoint_path"):
            if finetuning_type in PEFT_METHODS:  # list
                args["adapter_name_or_path"] = ",".join(
                    [get_save_dir(model_name, finetuning_type, adapter) for adapter in get("top.checkpoint_path")]
                )
            else:  # str
                args["model_name_or_path"] = get_save_dir(model_name, finetuning_type, get("top.checkpoint_path"))

        # quantization
        if get("top.quantization_bit") != "none":
            args["quantization_bit"] = int(get("top.quantization_bit"))
            args["quantization_method"] = get("top.quantization_method")
            args["double_quantization"] = not is_torch_npu_available()

        # freeze config
        if args["finetuning_type"] == "freeze":
            args["freeze_trainable_layers"] = get("train.freeze_trainable_layers")
            args["freeze_trainable_modules"] = get("train.freeze_trainable_modules")
            args["freeze_extra_modules"] = get("train.freeze_extra_modules") or None

        # lora config
        if args["finetuning_type"] == "lora":
            args["lora_rank"] = get("train.lora_rank")
            args["lora_alpha"] = get("train.lora_alpha")
            args["lora_dropout"] = get("train.lora_dropout")
            args["loraplus_lr_ratio"] = get("train.loraplus_lr_ratio") or None
            args["create_new_adapter"] = get("train.create_new_adapter")
            args["use_rslora"] = get("train.use_rslora")
            args["use_dora"] = get("train.use_dora")
            args["pissa_init"] = get("train.use_pissa")
            args["pissa_convert"] = get("train.use_pissa")
            args["lora_target"] = get("train.lora_target") or "all"
            args["additional_target"] = get("train.additional_target") or None

            if args["use_llama_pro"]:
                args["freeze_trainable_layers"] = get("train.freeze_trainable_layers")

        # rlhf config
        if args["stage"] == "ppo":
            if finetuning_type in PEFT_METHODS:
                args["reward_model"] = ",".join(
                    [get_save_dir(model_name, finetuning_type, adapter) for adapter in get("train.reward_model")]
                )
            else:
                args["reward_model"] = get_save_dir(model_name, finetuning_type, get("train.reward_model"))

            args["reward_model_type"] = "lora" if finetuning_type == "lora" else "full"
            args["ppo_score_norm"] = get("train.ppo_score_norm")
            args["ppo_whiten_rewards"] = get("train.ppo_whiten_rewards")
            args["top_k"] = 0
            args["top_p"] = 0.9
        elif args["stage"] in ["dpo", "kto"]:
            args["pref_beta"] = get("train.pref_beta")
            args["pref_ftx"] = get("train.pref_ftx")
            args["pref_loss"] = get("train.pref_loss")

        # multimodal config
        if model_name in MULTIMODAL_SUPPORTED_MODELS:
            args["freeze_vision_tower"] = get("train.freeze_vision_tower")
            args["freeze_multi_modal_projector"] = get("train.freeze_multi_modal_projector")
            args["freeze_language_model"] = get("train.freeze_language_model")
            args["image_max_pixels"] = calculate_pixels(get("train.image_max_pixels"))
            args["image_min_pixels"] = calculate_pixels(get("train.image_min_pixels"))
            args["video_max_pixels"] = calculate_pixels(get("train.video_max_pixels"))
            args["video_min_pixels"] = calculate_pixels(get("train.video_min_pixels"))

        # galore config
        if args["use_galore"]:
            args["galore_rank"] = get("train.galore_rank")
            args["galore_update_interval"] = get("train.galore_update_interval")
            args["galore_scale"] = get("train.galore_scale")
            args["galore_target"] = get("train.galore_target")

        # apollo config
        if args["use_apollo"]:
            args["apollo_rank"] = get("train.apollo_rank")
            args["apollo_update_interval"] = get("train.apollo_update_interval")
            args["apollo_scale"] = get("train.apollo_scale")
            args["apollo_target"] = get("train.apollo_target")

        # badam config
        if args["use_badam"]:
            args["badam_mode"] = get("train.badam_mode")
            args["badam_switch_mode"] = get("train.badam_switch_mode")
            args["badam_switch_interval"] = get("train.badam_switch_interval")
            args["badam_update_ratio"] = get("train.badam_update_ratio")

        # swanlab config
        if get("train.use_swanlab"):
            args["swanlab_project"] = get("train.swanlab_project")
            args["swanlab_run_name"] = get("train.swanlab_run_name")
            args["swanlab_workspace"] = get("train.swanlab_workspace")
            args["swanlab_api_key"] = get("train.swanlab_api_key")
            args["swanlab_mode"] = get("train.swanlab_mode")

        # eval config
        if get("train.val_size") > 1e-6 and args["stage"] != "ppo":
            args["val_size"] = get("train.val_size")
            args["eval_strategy"] = "steps"
            args["eval_steps"] = args["save_steps"]
            args["per_device_eval_batch_size"] = args["per_device_train_batch_size"]

        # ds config
        if get("train.ds_stage") != "none":
            ds_stage = get("train.ds_stage")
            ds_offload = "offload_" if get("train.ds_offload") else ""
            args["deepspeed"] = os.path.join(DEFAULT_CACHE_DIR, f"ds_z{ds_stage}_{ds_offload}config.json")

        return args