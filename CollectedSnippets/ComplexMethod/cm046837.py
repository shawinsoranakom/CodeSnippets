def _build_packed_training_setup(tmp_path, device):
    dtype = None
    if device.type == "cuda":
        if torch.cuda.is_bf16_supported():
            dtype = torch.bfloat16
        else:
            dtype = torch.float16

    try:
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name = "hf-internal-testing/tiny-random-LlamaForCausalLM",
            max_seq_length = 64,
            load_in_4bit = False,
            dtype = dtype,
        )
    except OSError as exc:  # pragma: no cover - offline CI
        pytest.skip(f"Requires access to tiny llama checkpoint: {exc}")

    model.to(device)

    dataset = Dataset.from_dict(
        {
            "text": [
                "Hello world!",
                "Short sample.",
                "This is a slightly longer packed example to test batching.",
                "Another response to include in the batch.",
            ]
        }
    )

    training_args = SFTConfig(
        per_device_train_batch_size = 1,
        per_device_eval_batch_size = 1,
        gradient_accumulation_steps = 1,
        dataset_text_field = "text",
        max_length = 64,
        logging_steps = 1,
        max_steps = 1,
        fp16 = device.type == "cuda" and not torch.cuda.is_bf16_supported(),
        bf16 = device.type == "cuda" and torch.cuda.is_bf16_supported(),
        dataset_num_proc = 1,
        output_dir = str(tmp_path),
        packing = True,
    )

    trainer = SFTTrainer(
        model = model,
        processing_class = tokenizer,
        train_dataset = dataset,
        args = training_args,
    )

    enable_sample_packing(model, trainer)

    dataloader = trainer.get_train_dataloader()
    batch = next(iter(dataloader))

    model_device = next(model.parameters()).device

    for key, value in list(batch.items()):
        if torch.is_tensor(value):
            batch[key] = value.to(model_device)

    from unsloth.models import llama as llama_mod

    return model, batch, trainer, llama_mod