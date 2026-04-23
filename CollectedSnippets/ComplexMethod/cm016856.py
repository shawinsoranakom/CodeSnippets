def execute(
        cls,
        model,
        latents,
        positive,
        batch_size,
        steps,
        grad_accumulation_steps,
        learning_rate,
        rank,
        optimizer,
        loss_function,
        seed,
        training_dtype,
        lora_dtype,
        quantized_backward,
        algorithm,
        gradient_checkpointing,
        checkpoint_depth,
        offloading,
        existing_lora,
        bucket_mode,
        bypass_mode,
    ):
        # Extract scalars from lists (due to is_input_list=True)
        model = model[0]
        batch_size = batch_size[0]
        steps = steps[0]
        grad_accumulation_steps = grad_accumulation_steps[0]
        learning_rate = learning_rate[0]
        rank = rank[0]
        optimizer_name = optimizer[0]
        loss_function_name = loss_function[0]
        seed = seed[0]
        training_dtype = training_dtype[0]
        lora_dtype = lora_dtype[0]
        quantized_backward = quantized_backward[0]
        algorithm = algorithm[0]
        gradient_checkpointing = gradient_checkpointing[0]
        offloading = offloading[0]
        checkpoint_depth = checkpoint_depth[0]
        existing_lora = existing_lora[0]
        bucket_mode = bucket_mode[0]
        bypass_mode = bypass_mode[0]

        comfy.model_management.training_fp8_bwd = quantized_backward

        # Process latents based on mode
        if bucket_mode:
            latents = _process_latents_bucket_mode(latents)
        else:
            latents = _process_latents_standard_mode(latents)

        # Process conditioning
        positive = _process_conditioning(positive)

        # Setup model and dtype
        mp = model.clone()
        use_grad_scaler = False
        lora_dtype = node_helpers.string_to_torch_dtype(lora_dtype)
        if training_dtype != "none":
            dtype = node_helpers.string_to_torch_dtype(training_dtype)
            mp.set_model_compute_dtype(dtype)
        else:
            # Detect model's native dtype for autocast
            model_dtype = mp.model.get_dtype()
            if model_dtype == torch.float16:
                dtype = torch.float16
                # GradScaler only supports float16 gradients, not bfloat16.
                # Only enable it when lora params will also be in float16.
                if lora_dtype != torch.bfloat16:
                    use_grad_scaler = True
                # Warn about fp16 accumulation instability during training
                if PerformanceFeature.Fp16Accumulation in args.fast:
                    logging.warning(
                        "WARNING: FP16 model detected with fp16_accumulation enabled. "
                        "This combination can be numerically unstable during training and may cause NaN values. "
                        "Suggested fixes: 1) Set training_dtype to 'bf16', or 2) Disable fp16_accumulation (remove from --fast flags)."
                    )
            else:
                # For fp8, bf16, or other dtypes, use bf16 autocast
                dtype = torch.bfloat16

        # Prepare latents and compute counts
        latents_dtype = dtype if dtype not in (None,) else torch.bfloat16
        latents, num_images, multi_res = _prepare_latents_and_count(
            latents, latents_dtype, bucket_mode
        )

        # Validate and expand conditioning
        positive = _validate_and_expand_conditioning(positive, num_images, bucket_mode)

        with torch.inference_mode(False):
            # Setup models for training
            mp.model.requires_grad_(False)

            # Load existing LoRA weights if provided
            existing_weights, existing_steps = _load_existing_lora(existing_lora)

            # Setup LoRA adapters
            bypass_manager = None
            if bypass_mode:
                logging.debug("Using bypass mode for training")
                lora_sd, all_weight_adapters, bypass_manager = _setup_lora_adapters_bypass(
                    mp, existing_weights, algorithm, lora_dtype, rank
                )
            else:
                lora_sd, all_weight_adapters = _setup_lora_adapters(
                    mp, existing_weights, algorithm, lora_dtype, rank
                )

            # Create optimizer and loss function
            optimizer = _create_optimizer(
                optimizer_name, lora_sd.values(), learning_rate
            )
            criterion = _create_loss_function(loss_function_name)

            # Setup gradient checkpointing
            if gradient_checkpointing:
                modules_to_patch = find_modules_at_depth(
                    mp.model.diffusion_model, depth=checkpoint_depth
                )
                logging.info(f"Gradient checkpointing: patching {len(modules_to_patch)} modules at depth {checkpoint_depth}")
                for m in modules_to_patch:
                    patch(m, offloading=offloading)

            torch.cuda.empty_cache()
            # With force_full_load=False we should be able to have offloading
            # But for offloading in training we need custom AutoGrad hooks for fwd/bwd
            comfy.model_management.load_models_gpu(
                [mp], memory_required=1e20, force_full_load=not offloading
            )
            torch.cuda.empty_cache()

            # Setup loss tracking
            loss_map = {"loss": []}

            def loss_callback(loss):
                loss_map["loss"].append(loss)

            # Create sampler
            if bucket_mode:
                train_sampler = TrainSampler(
                    criterion,
                    optimizer,
                    loss_callback=loss_callback,
                    batch_size=batch_size,
                    grad_acc=grad_accumulation_steps,
                    total_steps=steps * grad_accumulation_steps,
                    seed=seed,
                    training_dtype=dtype,
                    bucket_latents=latents,
                    use_grad_scaler=use_grad_scaler,
                )
            else:
                train_sampler = TrainSampler(
                    criterion,
                    optimizer,
                    loss_callback=loss_callback,
                    batch_size=batch_size,
                    grad_acc=grad_accumulation_steps,
                    total_steps=steps * grad_accumulation_steps,
                    seed=seed,
                    training_dtype=dtype,
                    real_dataset=latents if multi_res else None,
                    use_grad_scaler=use_grad_scaler,
                )

            # Setup guider
            guider = TrainGuider(mp, offloading=offloading)
            guider.set_conds(positive)

            # Inject bypass hooks if bypass mode is enabled
            bypass_injections = None
            if bypass_manager is not None:
                bypass_injections = bypass_manager.create_injections(mp.model)
                for injection in bypass_injections:
                    injection.inject(mp)
                logging.debug(f"[BypassMode] Injected {bypass_manager.get_hook_count()} bypass hooks")

            # Run training loop
            try:
                comfy.model_management.in_training = True
                _run_training_loop(
                    guider,
                    train_sampler,
                    latents,
                    num_images,
                    seed,
                    bucket_mode,
                    multi_res,
                )
            finally:
                comfy.model_management.in_training = False
                # Eject bypass hooks if they were injected
                if bypass_injections is not None:
                    for injection in bypass_injections:
                        injection.eject(mp)
                    logging.debug("[BypassMode] Ejected bypass hooks")
                for m in mp.model.modules():
                    unpatch(m)
            del train_sampler, optimizer

            for param in lora_sd:
                lora_sd[param] = lora_sd[param].to(lora_dtype).detach()

            for adapter in all_weight_adapters:
                adapter.requires_grad_(False)
                del adapter
            del all_weight_adapters

            # mp in train node is highly specialized for training
            # use it in inference will result in bad behavior so we don't return it
            return io.NodeOutput(lora_sd, loss_map, steps + existing_steps)