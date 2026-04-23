def main(*args):
    del args

    output_path = _OUTPUT_PATH.value
    variant = _VARIANT.value

    config = _VARIANTS[variant]
    config.text_config.dtype = getattr(torch, _TRANSFORMER_DTYPE.value)

    if _INCLUDE_VISION_ENCODER.value:
        config.vision_config.dtype = getattr(torch, _VISION_DTYPE.value)
    else:
        config.vision_config = None

    if _INCLUDE_CHAT_TEMPLATE.value:
        # Chat template is included for instruction tuned models, which treat
        # both "<eos>" and "<end_of_turn>" as generation stoppers.
        config.eos_token_id = [1, 106]

    logging.info(
        "Converting Gemma 3 (%s) @ %s (language) and %s (vision)",
        variant,
        _TRANSFORMER_DTYPE.value,
        _VISION_DTYPE.value,
    )
    state_tree, st_linears = convert(_CHECKPOINT_PATH.value, config, variant)
    logging.info("Converted Gemma 3 (%s) state tree from Orbax to Hugging Face.", variant)

    with accelerate.init_empty_weights():
        if variant == _VARIANT_EMBEDDINGGEMMA:
            model = Gemma3TextModel(config=config.text_config)
        elif _INCLUDE_VISION_ENCODER.value:
            model = Gemma3ForConditionalGeneration(config)
        else:
            model = Gemma3ForCausalLM(config=config.text_config)

    model.load_state_dict(state_tree, assign=True, strict=True)
    logging.info(
        "Loaded Gemma 3 (%s) in Hugging Face Transformers as a %s instance.",
        variant,
        type(model).__name__,
    )
    model.save_pretrained(output_path)
    logging.info(
        "Saved Gemma 3 (%s) to SafeTensors in %s using %s",
        variant,
        output_path,
        type(model).__name__,
    )
    del model
    del state_tree

    sentencepiece_extractor = SentencePieceExtractor(_TOKENIZER_PATH.value)
    vocab, _, merges = sentencepiece_extractor.extract()
    tokenizer = GemmaTokenizer(
        vocab=vocab,
        merges=merges,
        add_bos_token=True,
        add_eos_token=variant == _VARIANT_EMBEDDINGGEMMA,
        padding_side="right" if variant == _VARIANT_EMBEDDINGGEMMA else "left",
        extra_special_tokens={
            "image_token": "<image_soft_token>",  # Should be ID=262_144
            "boi_token": "<start_of_image>",  # Should be ID=255_999
            "eoi_token": "<end_of_image>",  # Should be ID=256_000
        },
        chat_template=get_chat_template(),
    )
    tokenizer.save_pretrained(output_path)
    logging.info("Saved GemmaTokenizer for %s to %s", variant, output_path)

    if _INCLUDE_VISION_ENCODER.value:
        image_processor = Gemma3ImageProcessor(
            image_seq_length=256,
            image_mean=(0.5,) * 3,
            image_std=(0.5,) * 3,
            size={"height": 896, "width": 896},
            resample=PILImageResampling.BILINEAR,
        )
        processor = Gemma3Processor(
            image_processor=image_processor,
            tokenizer=tokenizer,
            chat_template=tokenizer.chat_template,
        )
        processor.save_pretrained(output_path)
        logging.info("Saved Gemma3Processor for %s to %s", variant, output_path)
        del processor

    del tokenizer

    generation_config = GenerationConfig(
        pad_token_id=config.pad_token_id,
        bos_token_id=config.bos_token_id,
        eos_token_id=config.eos_token_id,
        cache_implementation="hybrid",
        temperature=1.0,
        do_sample=True,
        top_k=64,
        top_p=0.95,
    )
    generation_config.save_pretrained(output_path)

    if variant == _VARIANT_EMBEDDINGGEMMA:
        from sentence_transformers import SentenceTransformer, models

        # TODO: Support Retrieval tasks where we use `"title: {title} | text: {passage}"` interally and construct this
        # from split-records cached data, but externally these come through as a single string with components
        # separated by a newline. This should be used for `passage` for SentenceTransformers and the relevant MTEB
        # Retrieval tasks.
        # https://github.com/embeddings-benchmark/mteb/blob/main/docs/usage/usage.md#running-sentencetransformer-model-with-prompts
        task_prompts = {
            "query": "task: search result | query: ",
            "document": "title: none | text: ",
            "BitextMining": "task: search result | query: ",
            "Clustering": "task: clustering | query: ",
            "Classification": "task: classification | query: ",
            "InstructionRetrieval": "task: code retrieval | query: ",
            "MultilabelClassification": "task: classification | query: ",
            "PairClassification": "task: sentence similarity | query: ",
            "Reranking": "task: search result | query: ",
            "Retrieval": "task: search result | query: ",
            "Retrieval-query": "task: search result | query: ",
            "Retrieval-document": "title: none | text: ",
            "STS": "task: sentence similarity | query: ",
            "Summarization": "task: summarization | query: ",
        }

        transformer = models.Transformer(output_path)
        pooling = models.Pooling(config.text_config.hidden_size, pooling_mode="mean")
        normalize = models.Normalize()
        linears = []

        for linear_weight in st_linears:
            out_size, in_size = linear_weight.shape[:2]
            dense = models.Dense(in_size, out_size, bias=False, activation_function=None)
            dense.linear.weight.data = torch.from_numpy(linear_weight.astype("float32"))
            linears.append(dense)

        model = SentenceTransformer(modules=[transformer, pooling, *linears, normalize], prompts=task_prompts)
        model = model.to(getattr(torch, _TRANSFORMER_DTYPE.value))
        model.save_pretrained(output_path)