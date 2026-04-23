def _push_to_hub_gguf(
    self,
    repo_id,
    tokenizer = None,
    quantization_method = "fast_quantized",
    first_conversion = None,
    token = None,
    private = None,
    commit_message = "Upload GGUF SentenceTransformer model trained with Unsloth",
    commit_description = "Upload GGUF model trained with Unsloth 2x faster",
    max_shard_size = "5GB",
    temporary_location = "_unsloth_temporary_saved_buffers",
    maximum_memory_usage = 0.85,
    create_pr = False,
    revision = None,
    tags = None,
    **kwargs,
):
    """
    Converts the SentenceTransformer model to GGUF format and pushes to the Hugging Face Hub.

    This method:
    1. Saves the model locally to a temporary directory in GGUF format.
    2. Uploads the GGUF files, config, Ollama Modelfile, and README to the Hub.
    3. Cleans up the temporary directory.

    Args:
        repo_id (str): The Hugging Face Hub repo ID (e.g., "username/model-name").
        tokenizer: The tokenizer to save. Defaults to `self.tokenizer`.
        quantization_method (str or list): GGUF quantization method(s). Can be a string or list of strings.
            Choose from the following options:
            * "not_quantized"  : Recommended. Fast conversion. Slow inference, big files.
            * "fast_quantized" : Recommended. Fast conversion. OK inference, OK file size.
            * "quantized"      : Recommended. Slow conversion. Fast inference, small files.
            * "f32"     : Not recommended. Retains 100% accuracy, but super slow and memory hungry.
            * "f16"     : Fastest conversion + retains 100% accuracy. Slow and memory hungry.
            * "q8_0"    : Fast conversion. High resource use, but generally acceptable.
            * "q4_k_m"  : Recommended. Uses Q6_K for half of the attention.wv and feed_forward.w2 tensors, else Q4_K
            * "q5_k_m"  : Recommended. Uses Q6_K for half of the attention.wv and feed_forward.w2 tensors, else Q5_K
            * "q2_k"    : Uses Q4_K for the attention.vw and feed_forward.w2 tensors, Q2_K for the other tensors.
            * "q3_k_l"  : Uses Q5_K for the attention.wv, attention.wo, and feed_forward.w2 tensors, else Q3_K
            * "q3_k_m"  : Uses Q4_K for the attention.wv, attention.wo, and feed_forward.w2 tensors, else Q3_K
            * "q3_k_s"  : Uses Q3_K for all tensors
            * "q4_0"    : Original quant method, 4-bit.
            * "q4_1"    : Higher accuracy than q4_0 but not as high as q5_0. However has quicker inference than q5 models.
            * "q4_k_s"  : Uses Q4_K for all tensors
            * "q5_0"    : Higher accuracy, higher resource usage and slower inference.
            * "q5_1"    : Even higher accuracy, resource usage and slower inference.
            * "q5_k_s"  : Uses Q5_K for all tensors
            * "q6_k"    : Uses Q8_K for all tensors
        first_conversion (str, optional): The initial conversion format before quantization.
        token (str, optional): Hugging Face token. Uses cached token if not provided.
        private (bool, optional): Whether the repo should be private.
        commit_message (str): Commit message for the upload.
        commit_description (str): Commit description for the upload.
        max_shard_size (str): Maximum shard size for saving.
        temporary_location (str): Temp directory for intermediate files.
        maximum_memory_usage (float): Max fraction of memory to use.
        create_pr (bool): Whether to create a pull request instead of pushing directly.
        revision (str, optional): Branch/revision to push to.
        tags (list, optional): Additional tags for the repo.

    Returns:
        str: The full repo ID on Hugging Face Hub.
    """
    if token is None:
        token = get_token()
    if token is None:
        raise ValueError(
            "No HF token provided. Please provide a token or login with `huggingface-cli login`"
        )

    api = HfApi(token = token)

    # Determine full repo_id
    if "/" not in repo_id:
        username = api.whoami()["name"]
        full_repo_id = f"{username}/{repo_id}"
    else:
        full_repo_id = repo_id

    model_name = full_repo_id.split("/")[-1]

    # Create repo
    try:
        api.create_repo(
            repo_id = full_repo_id,
            private = private,
            exist_ok = True,
            repo_type = "model",
        )
    except Exception as e:
        print(f"Unsloth Warning: Could not create repo: {e}")

    # Save to temporary directory first
    with tempfile.TemporaryDirectory(prefix = "unsloth_st_gguf_") as temp_dir:
        print(f"Unsloth: Converting SentenceTransformer to GGUF format...")

        # Call save_pretrained_gguf to do the local conversion
        result = _save_pretrained_gguf(
            self,
            save_directory = temp_dir,
            tokenizer = tokenizer,
            quantization_method = quantization_method,
            first_conversion = first_conversion,
            push_to_hub = False,  # We handle upload ourselves
            token = token,
            max_shard_size = max_shard_size,
            temporary_location = temporary_location,
            maximum_memory_usage = maximum_memory_usage,
        )

        gguf_files = result.get("gguf_files", [])
        modelfile_location = result.get("modelfile_location", None)
        is_vlm = result.get("is_vlm", False)
        fix_bos_token = result.get("fix_bos_token", False)

        print(f"Unsloth: Uploading GGUF to https://huggingface.co/{full_repo_id}...")

        # Upload GGUF files
        for file_location in gguf_files:
            if os.path.exists(file_location):
                filename = os.path.basename(file_location)
                print(f"  Uploading {filename}...")
                api.upload_file(
                    path_or_fileobj = file_location,
                    path_in_repo = filename,
                    repo_id = full_repo_id,
                    repo_type = "model",
                    commit_message = commit_message,
                    commit_description = commit_description,
                    create_pr = create_pr,
                    revision = revision,
                )

        # Upload Modelfile if exists
        if modelfile_location and os.path.exists(modelfile_location):
            print("  Uploading Ollama Modelfile...")
            api.upload_file(
                path_or_fileobj = modelfile_location,
                path_in_repo = "Modelfile",
                repo_id = full_repo_id,
                repo_type = "model",
                commit_message = f"{commit_message} - Ollama Modelfile",
                create_pr = create_pr,
                revision = revision,
            )

        # Upload config.json if exists
        config_path = os.path.join(temp_dir, "config.json")
        if os.path.exists(config_path):
            print("  Uploading config.json...")
            api.upload_file(
                path_or_fileobj = config_path,
                path_in_repo = "config.json",
                repo_id = full_repo_id,
                repo_type = "model",
                commit_message = f"{commit_message} - config",
                create_pr = create_pr,
                revision = revision,
            )

        # Create and upload README
        gguf_basenames = [os.path.basename(f) for f in gguf_files if os.path.exists(f)]
        readme_content = f"""---
tags:
- gguf
- llama.cpp
- unsloth
- sentence-transformers
{"- vision-language-model" if is_vlm else ""}
---

# {model_name} - GGUF

This sentence-transformers model was finetuned and converted to GGUF format using [Unsloth](https://github.com/unslothai/unsloth).

## Available Model files:
"""
        for fname in gguf_basenames:
            readme_content += f"- `{fname}`\n"

        if modelfile_location and os.path.exists(modelfile_location):
            readme_content += "\n## Ollama\n"
            readme_content += "An Ollama Modelfile is included for easy deployment.\n"

        if fix_bos_token:
            readme_content += "\n## Note\n"
            readme_content += (
                "The model's BOS token behavior was adjusted for GGUF compatibility.\n"
            )

        readme_content += (
            "\nThis was trained 2x faster with [Unsloth](https://github.com/unslothai/unsloth)\n"
            '[<img src="https://raw.githubusercontent.com/unslothai/unsloth/main/images/unsloth%20made%20with%20love.png" width="200"/>](https://github.com/unslothai/unsloth)\n'
        )

        readme_path = os.path.join(temp_dir, "README.md")
        with open(readme_path, "w", encoding = "utf-8") as f:
            f.write(readme_content)

        api.upload_file(
            path_or_fileobj = readme_path,
            path_in_repo = "README.md",
            repo_id = full_repo_id,
            repo_type = "model",
            commit_message = "Add README",
            create_pr = create_pr,
            revision = revision,
        )

    # Add tags
    all_tags = ["gguf", "llama-cpp", "unsloth", "sentence-transformers"]
    if is_vlm:
        all_tags.append("vision-language-model")
    if tags is not None:
        if isinstance(tags, (list, tuple)):
            all_tags.extend(tags)
        else:
            all_tags.append(tags)
    try:
        api.add_tags(repo_id = full_repo_id, tags = all_tags, repo_type = "model")
    except:
        pass

    print(
        f"Unsloth: Successfully uploaded GGUF to https://huggingface.co/{full_repo_id}"
    )
    return full_repo_id