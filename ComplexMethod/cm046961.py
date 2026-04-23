def _construct_vlm_processor_fallback(
    tokenizer_name, model_type, token, trust_remote_code
):
    """Construct a VLM processor manually when AutoProcessor.from_pretrained fails.

    Some VLMs (e.g., LFM2.5-VL) have tokenizer_class entries that AutoTokenizer
    cannot resolve. This function loads the image processor and tokenizer separately,
    sets required special token attributes, and constructs the processor.
    """
    try:
        from transformers import AutoImageProcessor, PreTrainedTokenizerFast, AutoConfig
        from transformers.models.auto.processing_auto import PROCESSOR_MAPPING_NAMES
        import json

        # Load image processor
        image_processor = AutoImageProcessor.from_pretrained(
            tokenizer_name,
            token = token,
            trust_remote_code = trust_remote_code,
        )
        # Load tokenizer via PreTrainedTokenizerFast (bypasses tokenizer_class check)
        tok = PreTrainedTokenizerFast.from_pretrained(
            tokenizer_name,
            padding_side = "left",
            token = token,
            trust_remote_code = trust_remote_code,
        )
        # Read tokenizer_config.json for model-specific special tokens
        try:
            from huggingface_hub import hf_hub_download

            config_path = hf_hub_download(
                tokenizer_name, "tokenizer_config.json", token = token
            )
            with open(config_path, "r", encoding = "utf-8") as f:
                tok_config = json.load(f)
            # Set model-specific special tokens and their IDs
            for key in (
                "image_token",
                "image_start_token",
                "image_end_token",
                "image_thumbnail",
                "video_token",
            ):
                if key in tok_config and not hasattr(tok, key):
                    setattr(tok, key, tok_config[key])
                    id_key = key + "_id" if not key.endswith("_id") else key
                    token_id = tok.convert_tokens_to_ids(tok_config[key])
                    if not hasattr(tok, id_key):
                        setattr(tok, id_key, token_id)
        except Exception:
            pass

        # Find the processor class - try model_type first, then top-level config model_type
        proc_class_name = PROCESSOR_MAPPING_NAMES.get(model_type)
        if proc_class_name is None:
            # model_type might be a sub-model type (e.g. "lfm2" instead of "lfm2_vl").
            # Try the top-level config.model_type which often has the processor mapping.
            try:
                config = AutoConfig.from_pretrained(
                    tokenizer_name,
                    token = token,
                    trust_remote_code = trust_remote_code,
                )
                proc_class_name = PROCESSOR_MAPPING_NAMES.get(config.model_type)
            except Exception:
                pass

        if proc_class_name is not None:
            import transformers

            proc_class = getattr(transformers, proc_class_name, None)
            if proc_class is not None:
                processor = proc_class(image_processor = image_processor, tokenizer = tok)
                # Copy chat_template from tokenizer to processor if needed
                if not getattr(processor, "chat_template", None) and getattr(
                    tok, "chat_template", None
                ):
                    processor.chat_template = tok.chat_template
                return processor
    except Exception:
        pass
    return None