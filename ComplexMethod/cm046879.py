def unsloth_save_pretrained_gguf(
    self,
    save_directory: Union[str, os.PathLike],
    tokenizer = None,
    quantization_method = "fast_quantized",
    first_conversion: str = None,
    push_to_hub: bool = False,
    token: Optional[Union[str, bool]] = None,
    private: Optional[bool] = None,
    is_main_process: bool = True,
    state_dict: Optional[dict] = None,
    save_function: Callable = torch.save,
    max_shard_size: Union[int, str] = "5GB",
    safe_serialization: bool = True,
    variant: Optional[str] = None,
    save_peft_format: bool = True,
    tags: List[str] = None,
    temporary_location: str = "_unsloth_temporary_saved_buffers",
    maximum_memory_usage: float = 0.85,
):
    """
    Same as .save_pretrained(...) except 4bit weights are auto
    converted to float16 then converted to GGUF / llama.cpp format.

    Choose for `quantization_method` to be:
    "not_quantized"  : "Recommended. Fast conversion. Slow inference, big files.",
    "fast_quantized" : "Recommended. Fast conversion. OK inference, OK file size.",
    "quantized"      : "Recommended. Slow conversion. Fast inference, small files.",
    "f32"     : "Not recommended. Retains 100% accuracy, but super slow and memory hungry.",
    "f16"     : "Fastest conversion + retains 100% accuracy. Slow and memory hungry.",
    "q8_0"    : "Fast conversion. High resource use, but generally acceptable.",
    "q4_k_m"  : "Recommended. Uses Q6_K for half of the attention.wv and feed_forward.w2 tensors, else Q4_K",
    "q5_k_m"  : "Recommended. Uses Q6_K for half of the attention.wv and feed_forward.w2 tensors, else Q5_K",
    "q2_k"    : "Uses Q4_K for the attention.vw and feed_forward.w2 tensors, Q2_K for the other tensors.",
    "q2_k_l"  : "Q2_K_L with --output-tensor-type q8_0 --token-embedding-type q8_0.",
    "q3_k_l"  : "Uses Q5_K for the attention.wv, attention.wo, and feed_forward.w2 tensors, else Q3_K",
    "q3_k_m"  : "Uses Q4_K for the attention.wv, attention.wo, and feed_forward.w2 tensors, else Q3_K",
    "q3_k_s"  : "Uses Q3_K for all tensors",
    "q4_0"    : "Original quant method, 4-bit.",
    "q4_1"    : "Higher accuracy than q4_0 but not as high as q5_0. However has quicker inference than q5 models.",
    "q4_k_s"  : "Uses Q4_K for all tensors",
    "q4_k"    : "alias for q4_k_m",
    "q5_k"    : "alias for q5_k_m",
    "q5_0"    : "Higher accuracy, higher resource usage and slower inference.",
    "q5_1"    : "Even higher accuracy, resource usage and slower inference.",
    "q5_k_s"  : "Uses Q5_K for all tensors",
    "q6_k"    : "Uses Q8_K for all tensors",
    "iq2_xxs" : "2.06 bpw quantization",
    "iq2_xs"  : "2.31 bpw quantization",
    "iq3_xxs" : "3.06 bpw quantization",
    "q3_k_xs" : "3-bit extra small quantization",
    """
    if tokenizer is None:
        raise ValueError("Unsloth: Saving to GGUF must have a tokenizer.")
    if isinstance(tokenizer, (PreTrainedTokenizerBase, ProcessorMixin)):
        tokenizer = patch_saving_functions(tokenizer)

    try:
        base_model_name = get_model_name(self.config._name_or_path, load_in_4bit = False)
        model_name = base_model_name.split("/")[-1]
    except:
        base_model_name = self.config._name_or_path
        model_name = base_model_name.split("/")[-1]

    # Check if push_to_hub is requested
    if push_to_hub:
        raise ValueError(
            "Unsloth: Please use .push_to_hub_gguf() instead of .save_pretrained_gguf() with push_to_hub=True"
        )

    # Step 1: Check if this is a VLM (Vision-Language Model) and check if gpt-oss
    is_vlm = False
    if hasattr(self, "config") and hasattr(self.config, "architectures"):
        is_vlm = any(
            x.endswith(("ForConditionalGeneration", "ForVisionText2Text"))
            for x in self.config.architectures
        )
        is_vlm = is_vlm or hasattr(self.config, "vision_config")

    is_processor = is_vlm and isinstance(tokenizer, ProcessorMixin)

    is_gpt_oss = (
        True
        if (
            hasattr(self.config, "architectures")
            and self.config.architectures == "GptOssForCausalLM"
        )
        or (
            hasattr(self.config, "model_type")
            and self.config.model_type in ["gpt-oss", "gpt_oss"]
        )
        else False
    )
    # Step 2: Prepare arguments for model saving
    arguments = dict(locals())
    arguments["model"] = self
    arguments["tokenizer"] = tokenizer
    arguments["push_to_hub"] = False  # We handle upload ourselves
    # GPT-OSS needs mxfp4 save method
    if is_gpt_oss:
        if quantization_method is not None:
            _qm = (
                quantization_method
                if isinstance(quantization_method, (list, tuple))
                else [quantization_method]
            )
            _ignored = [q for q in _qm if str(q).lower() != "mxfp4"]
            if _ignored:
                logger.warning_once(
                    f"Unsloth: GPT-OSS does not support GGUF quantization "
                    f"(requested: {', '.join(str(q) for q in _ignored)}). "
                    f"Overriding to MXFP4 format. "
                    f"Pass quantization_method=None to suppress this warning."
                )
        arguments["save_method"] = "mxfp4"
    else:
        arguments["save_method"] = "merged_16bit"
    del arguments["self"]
    del arguments["quantization_method"]
    del arguments["first_conversion"]
    del arguments["is_vlm"]
    del arguments["is_gpt_oss"]
    del arguments["model_name"]
    del arguments["base_model_name"]
    del arguments["is_processor"]

    # Step 3: Fix tokenizer BOS token if needed
    if is_processor:
        fix_bos_token, old_chat_template = fix_tokenizer_bos_token(tokenizer.tokenizer)
    else:
        fix_bos_token, old_chat_template = fix_tokenizer_bos_token(tokenizer)

    # Step 4: Save/merge model to 16-bit format
    is_peft_model = isinstance(self, PeftModelForCausalLM) or isinstance(
        self, PeftModel
    )

    if is_peft_model:
        print(
            f'Unsloth: Merging model weights to {"mxfp4" if is_gpt_oss else "16-bit"} format...'
        )
        try:
            # Call unsloth_generic_save directly (it's in the same file)
            unsloth_generic_save(**arguments)

        except Exception as e:
            raise RuntimeError(f"Failed to save/merge model: {e}")
    else:
        # Non-PEFT model — checkpoint files already exist on disk.
        # Point save_to_gguf at the original checkpoint path instead of
        # re-saving to a temporary "model" subdirectory.
        original_path = getattr(self.config, "_name_or_path", None)
        if original_path and os.path.isdir(original_path):
            print(
                f"Unsloth: Model is not a PEFT model. Using existing checkpoint at {original_path}"
            )
            save_directory = original_path
            # Persist tokenizer fixes (e.g. BOS token stripping) to disk
            # so the GGUF converter picks up the corrected chat template.
            if tokenizer is not None:
                tokenizer.save_pretrained(save_directory)
        else:
            # Fallback: save the in-memory model to save_directory
            print(
                "Unsloth: Model is not a PEFT model. Saving directly without LoRA merge..."
            )
            os.makedirs(save_directory, exist_ok = True)
            try:
                self.save_pretrained(save_directory)
                if tokenizer is not None:
                    tokenizer.save_pretrained(save_directory)
            except Exception as e:
                raise RuntimeError(f"Failed to save model: {e}")

    if is_processor:
        tokenizer = tokenizer.tokenizer

    # Use old chat template if the bos is removed
    if fix_bos_token:
        tokenizer.chat_template = old_chat_template

    # Step 6: Clean up memory
    for _ in range(3):
        import gc

        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    # Step 7: Get model dtype and type
    try:
        model_dtype = dtype_from_config(self.config)
        model_type = self.config.model_type
        if type(model_dtype) is str:
            assert model_dtype == "float16" or model_dtype == "bfloat16"
        elif model_dtype == torch.float16:
            model_dtype = "float16"
        elif model_dtype == torch.bfloat16:
            model_dtype = "bfloat16"
        else:
            raise TypeError("Unsloth: Model dtype can only be float16 or bfloat16")
    except Exception as e:
        # Fallback if dtype_from_config fails
        print(f"Unsloth: Could not determine dtype ({e}), defaulting to float16")
        model_dtype = "float16"

    # Step 8: Convert to GGUF format
    print("Unsloth: Converting to GGUF format...")

    # Convert quantization_method to list if string
    # Use old style quantization_method
    quantization_methods = []
    if quantization_method is not None:
        # Convert quantization_method to list
        if isinstance(quantization_method, list):
            pass
        elif isinstance(quantization_method, str):
            quantization_method = [
                quantization_method,
            ]
        elif isinstance(quantization_method, tuple):
            quantization_method = list(quantization_method)
        else:
            raise TypeError(
                "Unsloth: quantization_method can only be a string or a list of strings"
            )
        for i, quant_method in enumerate(quantization_method):
            quant_method = quant_method.lower()
            if quant_method == "not_quantized":
                quant_method = "f16"
            elif quant_method == "fast_quantized":
                quant_method = "q8_0"
            elif quant_method == "quantized":
                quant_method = "q4_k_m"
            elif quant_method is None:
                quant_method = "q8_0"
            quantization_methods.append(quant_method.lower())

    try:
        all_file_locations, want_full_precision, is_vlm_update = save_to_gguf(
            model_name = model_name,
            model_type = model_type,
            model_dtype = model_dtype,
            is_sentencepiece = False,
            model_directory = save_directory,
            quantization_method = quantization_methods,
            first_conversion = first_conversion,
            is_vlm = is_vlm,  # Pass VLM flag
            is_gpt_oss = is_gpt_oss,  # Pass gpt_oss Flag
        )
    except Exception as e:
        if IS_KAGGLE_ENVIRONMENT:
            raise RuntimeError(
                f"Unsloth: GGUF conversion failed in Kaggle environment.\n"
                f"This is likely due to the 20GB disk space limit.\n"
                f"Try saving to /tmp directory or use a smaller model.\n"
                f"Error: {e}"
            )
        else:
            raise RuntimeError(f"Unsloth: GGUF conversion failed: {e}")

    # Step 9: Create Ollama modelfile
    gguf_directory = f"{save_directory}_gguf"
    modelfile_location = None
    ollama_success = False
    if all_file_locations:
        try:
            if is_vlm_update:
                modelfile = create_ollama_modelfile(tokenizer, base_model_name, ".")
            else:
                modelfile = create_ollama_modelfile(
                    tokenizer,
                    base_model_name,
                    os.path.basename(all_file_locations[0]),
                )
            if modelfile is not None:
                modelfile_location = os.path.join(gguf_directory, "Modelfile")
                with open(modelfile_location, "w", encoding = "utf-8") as file:
                    file.write(modelfile)
                ollama_success = True
        except Exception as e:
            print(f"Warning: Could not create Ollama modelfile: {e}")

    # Step 10: Show BOS token warning if applicable
    if fix_bos_token:
        logger.warning(
            "Unsloth: ##### The current model auto adds a BOS token.\n"
            "Unsloth: ##### We removed it in GGUF's chat template for you."
        )

    _exe = ".exe" if IS_WINDOWS else ""
    if IS_WINDOWS:
        _bin_dir = os.path.join(LLAMA_CPP_DEFAULT_DIR, "build", "bin", "Release")
    else:
        _bin_dir = LLAMA_CPP_DEFAULT_DIR

    if is_vlm_update:
        print("\n")
        print(
            f"Unsloth: example usage for Multimodal LLMs: {os.path.join(_bin_dir, 'llama-mtmd-cli' + _exe)} -m {all_file_locations[0]} --mmproj {all_file_locations[-1]}"
        )
        print("Unsloth: load image inside llama.cpp runner: /image test_image.jpg")
        print("Unsloth: Prompt model to describe the image")
    else:
        print(
            f'Unsloth: example usage for text only LLMs: {os.path.join(_bin_dir, "llama-cli" + _exe)} --model {all_file_locations[0]} -p "why is the sky blue?"'
        )

    if ollama_success:
        print(f"Unsloth: Saved Ollama Modelfile to {modelfile_location}")
        print(
            f"Unsloth: convert model to ollama format by running - ollama create model_name -f {modelfile_location}"
        )

    # Return a dict with all needed info for push_to_hub
    return {
        "save_directory": save_directory,
        "gguf_directory": gguf_directory,
        "gguf_files": all_file_locations,
        "modelfile_location": modelfile_location,
        "want_full_precision": want_full_precision,
        "is_vlm": is_vlm_update,
        "fix_bos_token": fix_bos_token,
    }