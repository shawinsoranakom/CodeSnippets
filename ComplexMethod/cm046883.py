def save_to_gguf_generic(
    model,
    save_directory,
    tokenizer,
    quantization_method = None,
    quantization_type = "Q8_0",
    repo_id = None,
    token = None,
):
    if token is None and repo_id is not None:
        token = get_token()
    if repo_id is not None and token is None:
        raise RuntimeError("Unsloth: Please specify a token for uploading!")

    if not os.path.exists(os.path.join("llama.cpp", "unsloth_convert_hf_to_gguf.py")):
        install_llama_cpp(just_clone_repo = True)

    # Use old style quantization_method
    new_quantization_methods = []
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
            new_quantization_methods.append(quant_method.lower())
    else:
        new_quantization_methods.append(quantization_type.lower())
    # Check if wrong method
    for quant_method in new_quantization_methods:
        if quant_method not in ALLOWED_QUANTS.keys():
            error = f"Unsloth: Quant method = [{quant_method}] not supported. Choose from below:\n"
            for key, value in ALLOWED_QUANTS.items():
                error += f"[{key}] => {value}\n"
            raise RuntimeError(error)

    # Go through all types and save individually - somewhat inefficient
    # since we save F16 / BF16 multiple times
    for quantization_type in new_quantization_methods:
        metadata = _convert_to_gguf(
            save_directory,
            print_output = True,
            quantization_type = quantization_type,
        )
        if repo_id is not None:
            prepare_saving(
                model,
                repo_id,
                push_to_hub = True,
                max_shard_size = "50GB",
                private = True,
                token = token,
            )

            from huggingface_hub import HfApi

            api = HfApi(token = token)
            api.upload_folder(
                folder_path = save_directory,
                repo_id = repo_id,
                repo_type = "model",
                allow_patterns = ["*.gguf"],
            )
    return metadata