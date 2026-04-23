def unsloth_push_to_hub_gguf(
    self,
    repo_id: str,
    tokenizer = None,
    quantization_method = "fast_quantized",
    first_conversion: str = None,
    use_temp_dir: Optional[bool] = None,
    commit_message: Optional[str] = "Trained with Unsloth",
    private: Optional[bool] = None,
    token: Union[bool, str, None] = None,
    max_shard_size: Union[int, str, None] = "5GB",
    create_pr: bool = False,
    safe_serialization: bool = True,
    revision: str = None,
    commit_description: str = "Upload model trained with Unsloth 2x faster",
    tags: Optional[List[str]] = None,
    temporary_location: str = "_unsloth_temporary_saved_buffers",
    maximum_memory_usage: float = 0.85,
    datasets: Optional[List[str]] = None,
):
    """
    Same as .push_to_hub(...) except 4bit weights are auto
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
    "q5_0"    : "Higher accuracy, higher resource usage and slower inference.",
    "q5_1"    : "Even higher accuracy, resource usage and slower inference.",
    "q5_k_s"  : "Uses Q5_K for all tensors",
    "q6_k"    : "Uses Q8_K for all tensors",
    """
    if tokenizer is None:
        raise ValueError("Unsloth: Saving to GGUF must have a tokenizer.")

    # Step 1: Determine save directory
    model_name = repo_id.split("/")[-1] if "/" in repo_id else repo_id

    if use_temp_dir or use_temp_dir is None:
        import tempfile

        temp_dir = tempfile.mkdtemp(prefix = "unsloth_gguf_")
        save_directory = temp_dir
        cleanup_temp = True
    else:
        save_directory = model_name  # Use model name, not repo_id
        cleanup_temp = False

    # Step 2: Call save_pretrained_gguf to do the conversion
    print(f"Unsloth: Converting model to GGUF format...")

    try:
        # Call save_pretrained_gguf - it returns all the info we need
        result = unsloth_save_pretrained_gguf(
            self = self,
            save_directory = save_directory,
            tokenizer = tokenizer,
            quantization_method = quantization_method,
            first_conversion = first_conversion,
            push_to_hub = False,  # Never push from here
            token = None,  # Don't need token for local save
            max_shard_size = max_shard_size,
            safe_serialization = safe_serialization,
            temporary_location = temporary_location,
            maximum_memory_usage = maximum_memory_usage,
        )

        # Extract results
        all_file_locations = result["gguf_files"]
        modelfile_location = result["modelfile_location"]
        want_full_precision = result["want_full_precision"]
        is_vlm = result["is_vlm"]
        fix_bos_token = result["fix_bos_token"]
        actual_save_directory = result["save_directory"]

    except Exception as e:
        if cleanup_temp:
            import shutil

            for d in [save_directory, f"{save_directory}_gguf"]:
                try:
                    shutil.rmtree(d)
                except:
                    pass
        raise RuntimeError(f"Failed to convert model to GGUF: {e}")

    # Step 3: Upload to HuggingFace Hub
    print("Unsloth: Uploading GGUF to Huggingface Hub...")

    try:
        from huggingface_hub import HfApi

        api = HfApi(token = token)

        # Get full repo id
        if "/" not in repo_id:
            username = api.whoami()["name"]
            full_repo_id = f"{username}/{repo_id}"
        else:
            full_repo_id = repo_id

        # Create repo
        api.create_repo(
            repo_id = full_repo_id,
            repo_type = "model",
            private = private,
            exist_ok = True,
        )

        # Upload GGUF files
        for file_location in all_file_locations:
            original_name = os.path.basename(file_location)
            # Replace temp directory name with proper model name
            if cleanup_temp and "unsloth_gguf_" in original_name:
                # Extract the quantization part (e.g., ".Q8_0.gguf" or ".Q8_0-mmproj.gguf")
                quant_suffix = (
                    original_name.split(".", 1)[1]
                    if "." in original_name
                    else original_name
                )
                proper_name = f"{model_name}.{quant_suffix}"
            else:
                proper_name = original_name.replace(
                    os.path.basename(save_directory), model_name
                )

            print(f"Uploading {proper_name}...")

            api.upload_file(
                path_or_fileobj = file_location,
                path_in_repo = proper_name,
                repo_id = full_repo_id,
                repo_type = "model",
                commit_message = commit_message,
                commit_description = commit_description,
                create_pr = create_pr,
                revision = revision,
            )

        # Upload config.json if exists
        config_path = os.path.join(actual_save_directory, "config.json")
        if os.path.exists(config_path):
            print("Uploading config.json...")
            api.upload_file(
                path_or_fileobj = config_path,
                path_in_repo = "config.json",
                repo_id = full_repo_id,
                repo_type = "model",
                commit_message = f"{commit_message} - config",
                create_pr = create_pr,
                revision = revision,
            )

        # Upload Modelfile if exists
        if modelfile_location and os.path.exists(modelfile_location):
            print("Uploading Ollama Modelfile...")
            api.upload_file(
                path_or_fileobj = modelfile_location,
                path_in_repo = "Modelfile",
                repo_id = full_repo_id,
                repo_type = "model",
                commit_message = f"{commit_message} - Ollama Modelfile",
                create_pr = create_pr,
                revision = revision,
            )

        # Create and upload README
        readme_content = f"""---
tags:
- gguf
- llama.cpp
- unsloth
{"- vision-language-model" if is_vlm else ""}
---

# {repo_id.split("/")[-1]} : GGUF

This model was finetuned and converted to GGUF format using [Unsloth](https://github.com/unslothai/unsloth).

**Example usage**:
- For text only LLMs:    `llama-cli -hf {repo_id} --jinja`
- For multimodal models: `llama-mtmd-cli -hf {repo_id} --jinja`

## Available Model files:
"""
        for file in all_file_locations:
            # Fix filename in README too
            original_name = os.path.basename(file)
            if cleanup_temp and "unsloth_gguf_" in original_name:
                quant_suffix = (
                    original_name.split(".", 1)[1]
                    if "." in original_name
                    else original_name
                )
                proper_name = f"{model_name}.{quant_suffix}"
            else:
                proper_name = original_name.replace(
                    os.path.basename(save_directory), model_name
                )
            readme_content += f"- `{proper_name}`\n"

        # Special note for VLM with Modelfile
        if is_vlm and modelfile_location:
            readme_content += "\n## ⚠️ Ollama Note for Vision Models\n"
            readme_content += "**Important:** Ollama currently does not support separate mmproj files for vision models.\n\n"
            readme_content += "To create an Ollama model from this vision model:\n"
            readme_content += "1. Place the `Modelfile` in the same directory as the finetuned bf16 merged model\n"
            readme_content += "3. Run: `ollama create model_name -f ./Modelfile`\n"
            readme_content += "   (Replace `model_name` with your desired name)\n\n"
            readme_content += (
                "This will create a unified bf16 model that Ollama can use.\n"
            )
        elif modelfile_location:
            readme_content += "\n## Ollama\n"
            readme_content += "An Ollama Modelfile is included for easy deployment.\n"

        if fix_bos_token:
            readme_content += "\n## Note\n"
            readme_content += (
                "The model's BOS token behavior was adjusted for GGUF compatibility.\n"
            )

        readme_content += (
            "This was trained 2x faster with [Unsloth](https://github.com/unslothai/unsloth)\n"
            '[<img src="https://raw.githubusercontent.com/unslothai/unsloth/main/images/unsloth%20made%20with%20love.png" width="200"/>](https://github.com/unslothai/unsloth)\n'
        )

        readme_path = os.path.join(actual_save_directory, "README.md")
        with open(readme_path, "w") as f:
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

        print(
            f"Unsloth: Successfully uploaded GGUF to https://huggingface.co/{full_repo_id}"
        )

        # Add tags
        if tags is None:
            tags = []
        tags.extend(["gguf", "llama-cpp", "unsloth"])
        if is_vlm:
            tags.append("vision-language-model")

        try:
            api.add_tags(
                repo_id = full_repo_id,
                tags = tags,
                repo_type = "model",
            )
        except:
            pass

        if datasets:
            try:
                from huggingface_hub import metadata_update

                metadata_update(
                    full_repo_id, {"datasets": datasets}, overwrite = True, token = token
                )
            except Exception as e:
                logger.warning_once(
                    f"Unsloth: Could not update datasets metadata for {full_repo_id}: {e}"
                )

    except Exception as e:
        raise RuntimeError(f"Failed to upload to Hugging Face Hub: {e}")

    finally:
        # Clean up temporary directory
        if cleanup_temp:
            print("Unsloth: Cleaning up temporary files...")
            import shutil

            for d in [save_directory, f"{save_directory}_gguf"]:
                if os.path.exists(d):
                    try:
                        shutil.rmtree(d)
                    except:
                        pass

    return full_repo_id