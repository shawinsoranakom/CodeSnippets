def run(args):
    from unsloth import FastLanguageModel
    from datasets import load_dataset
    from transformers.utils import strtobool
    from trl import SFTTrainer, SFTConfig
    from unsloth import is_bfloat16_supported
    from unsloth.models.loader_utils import prepare_device_map
    import logging
    from unsloth import RawTextDataLoader

    logging.getLogger("hf-to-gguf").setLevel(logging.WARNING)

    # Load model and tokenizer
    device_map, distributed = prepare_device_map()
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name = args.model_name,
        max_seq_length = args.max_seq_length,
        dtype = args.dtype,
        load_in_4bit = args.load_in_4bit,
        device_map = device_map,
    )

    # Configure PEFT model
    model = FastLanguageModel.get_peft_model(
        model,
        r = args.r,
        target_modules = [
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ],
        lora_alpha = args.lora_alpha,
        lora_dropout = args.lora_dropout,
        bias = args.bias,
        use_gradient_checkpointing = args.use_gradient_checkpointing,
        random_state = args.random_state,
        use_rslora = args.use_rslora,
        loftq_config = args.loftq_config,
    )

    alpaca_prompt = """Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

    ### Instruction:
    {}

    ### Input:
    {}

    ### Response:
    {}"""

    EOS_TOKEN = tokenizer.eos_token  # Must add EOS_TOKEN

    def formatting_prompts_func(examples):
        instructions = examples["instruction"]
        inputs = examples["input"]
        outputs = examples["output"]
        texts = []
        for instruction, input, output in zip(instructions, inputs, outputs):
            text = alpaca_prompt.format(instruction, input, output) + EOS_TOKEN
            texts.append(text)
        return {"text": texts}

    def load_dataset_smart(args):
        from transformers.utils import strtobool

        if args.raw_text_file:
            # Use raw text loader
            loader = RawTextDataLoader(tokenizer, args.chunk_size, args.stride)
            dataset = loader.load_from_file(args.raw_text_file)
        elif args.dataset.endswith((".txt", ".md", ".json", ".jsonl")):
            # Auto-detect local raw text files
            loader = RawTextDataLoader(tokenizer)
            dataset = loader.load_from_file(args.dataset)
        else:
            # Check for modelscope usage
            use_modelscope = strtobool(
                os.environ.get("UNSLOTH_USE_MODELSCOPE", "False")
            )
            if use_modelscope:
                from modelscope import MsDataset

                dataset = MsDataset.load(args.dataset, split = "train")
            else:
                # Existing HuggingFace dataset logic
                dataset = load_dataset(args.dataset, split = "train")

            # Apply formatting for structured datasets
            dataset = dataset.map(formatting_prompts_func, batched = True)
        return dataset

    # Load dataset using smart loader
    dataset = load_dataset_smart(args)
    print("Data is formatted and ready!")

    # Configure training arguments
    training_args = SFTConfig(
        per_device_train_batch_size = args.per_device_train_batch_size,
        per_device_eval_batch_size = args.per_device_eval_batch_size,
        gradient_accumulation_steps = args.gradient_accumulation_steps,
        warmup_steps = args.warmup_steps,
        max_steps = args.max_steps,
        learning_rate = args.learning_rate,
        fp16 = not is_bfloat16_supported(),
        bf16 = is_bfloat16_supported(),
        logging_steps = args.logging_steps,
        optim = args.optim,
        weight_decay = args.weight_decay,
        lr_scheduler_type = args.lr_scheduler_type,
        seed = args.seed,
        output_dir = args.output_dir,
        report_to = args.report_to,
        max_length = args.max_seq_length,
        dataset_num_proc = 2,
        ddp_find_unused_parameters = False if distributed else None,
        packing = args.packing,
    )

    # Initialize trainer
    trainer = SFTTrainer(
        model = model,
        processing_class = tokenizer,
        train_dataset = dataset,
        args = training_args,
    )

    trainer.train()

    # Save model
    if args.save_model:
        # if args.quantization_method is a list, we will save the model for each quantization method
        if args.save_gguf:
            if isinstance(args.quantization, list):
                for quantization_method in args.quantization:
                    print(
                        f"Saving model with quantization method: {quantization_method}"
                    )
                    model.save_pretrained_gguf(
                        args.save_path,
                        tokenizer,
                        quantization_method = quantization_method,
                    )
                    if args.push_model:
                        model.push_to_hub_gguf(
                            hub_path = args.hub_path,
                            hub_token = args.hub_token,
                            quantization_method = quantization_method,
                        )
            else:
                print(f"Saving model with quantization method: {args.quantization}")
                model.save_pretrained_gguf(
                    args.save_path,
                    tokenizer,
                    quantization_method = args.quantization,
                )
                if args.push_model:
                    model.push_to_hub_gguf(
                        hub_path = args.hub_path,
                        hub_token = args.hub_token,
                        quantization_method = args.quantization,
                    )
        else:
            model.save_pretrained_merged(args.save_path, tokenizer, args.save_method)
            if args.push_model:
                model.push_to_hub_merged(args.save_path, tokenizer, args.hub_token)
    else:
        print("Warning: The model is not saved!")