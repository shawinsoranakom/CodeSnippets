def _save_pretrained_gguf(
    self,
    save_directory,
    tokenizer = None,
    quantization_method = "fast_quantized",
    first_conversion = None,
    push_to_hub = False,
    token = None,
    max_shard_size = "5GB",
    temporary_location = "_unsloth_temporary_saved_buffers",
    maximum_memory_usage = 0.85,
    **kwargs,
):
    """
    Saves the SentenceTransformer model to GGUF format by saving the inner transformer model,
    converting it, and placing the resulting GGUF files in the save directory.
    """
    # 1. Save standard SentenceTransformer structure (configs, modules.json, etc.)
    self.save_pretrained(save_directory)

    # 2. Extract inner transformer model
    inner_model = self[0].auto_model
    if hasattr(inner_model, "_orig_mod"):
        inner_model = inner_model._orig_mod

    # If it's a PEFT model, unsloth_save_pretrained_gguf handles merging,
    # but we pass the inner model wrapper.

    # 3. Identify where the transformer weights are stored
    transformer_path = "0_Transformer"
    modules_path = os.path.join(save_directory, "modules.json")
    if os.path.exists(modules_path):
        try:
            with open(modules_path, "r") as f:
                modules = json.load(f)
            for m in modules:
                if m.get("type", "").endswith("Transformer"):
                    transformer_path = m.get("path", "")
                    break
        except:
            pass

    # This is where Unsloth will perform the save + conversion operations
    transformer_dir = os.path.join(save_directory, transformer_path)
    # Ensure this path is absolute for consistent comparison later
    transformer_dir = os.path.abspath(transformer_dir)

    if tokenizer is None:
        tokenizer = self.tokenizer

    # 4. Patch environment to ensure Unsloth treats this embedding model correctly
    @contextlib.contextmanager
    def patch_unsloth_gguf_save():
        # Prevent deletion of the directory we just created via self.save_pretrained
        original_rmtree = shutil.rmtree
        try:
            yield
        finally:
            shutil.rmtree = original_rmtree

    # 5. Call Unsloth's GGUF saver on the inner model targeting the transformer subdirectory
    with patch_unsloth_gguf_save():
        result = unsloth_save_pretrained_gguf(
            inner_model,
            save_directory = transformer_dir,
            tokenizer = tokenizer,
            quantization_method = quantization_method,
            first_conversion = first_conversion,
            push_to_hub = False,  # Force local first to move files
            token = token,
            max_shard_size = max_shard_size,
            temporary_location = temporary_location,
            maximum_memory_usage = maximum_memory_usage,
        )

    # 6. Move GGUF files from the subdirectory (0_Transformer) to the root save_directory
    gguf_files = result.get("gguf_files", [])

    new_gguf_locations = []

    for gguf_file in gguf_files:
        if os.path.exists(gguf_file):
            filename = os.path.basename(gguf_file)
            dest_path = os.path.join(save_directory, filename)

            # Convert to absolute path to avoid mixing relative/absolute in commonpath
            abs_gguf_file = os.path.abspath(gguf_file)

            # Check if file is inside transformer_dir (subpath)
            try:
                is_subpath = (
                    os.path.commonpath([abs_gguf_file, transformer_dir])
                    == transformer_dir
                )
            except ValueError:
                # Can happen on Windows with different drives, or mix of absolute/relative (handled by abspath above)
                is_subpath = False

            if is_subpath:
                # If the GGUF file is inside the transformer_dir, move it out to root
                shutil.move(gguf_file, dest_path)
                new_gguf_locations.append(dest_path)
            else:
                # If it's elsewhere, move it to root if not already there
                if os.path.abspath(dest_path) != abs_gguf_file:
                    shutil.move(gguf_file, dest_path)
                new_gguf_locations.append(dest_path)

    # Update result with new locations
    result["gguf_files"] = new_gguf_locations

    # 7. Add branding
    try:
        FastSentenceTransformer._add_unsloth_branding(save_directory)

        # Add GGUF details to README
        readme_path = os.path.join(save_directory, "README.md")
        if os.path.exists(readme_path):
            with open(readme_path, "a", encoding = "utf-8") as f:
                f.write("\n## GGUF Quantization\n")
                f.write(
                    f"This model contains GGUF quantized versions in: {', '.join([os.path.basename(f) for f in new_gguf_locations])}\n"
                )
    except:
        pass

    # 8. Handle Push to Hub if requested
    if push_to_hub:
        if token is None:
            token = get_token()

        api = HfApi(token = token)
        repo_id = save_directory  # Assuming save_directory is the repo name if pushing

        print(f"Unsloth: Uploading to {repo_id}...")
        try:
            api.create_repo(
                repo_id = repo_id, exist_ok = True, private = kwargs.get("private", False)
            )
            api.upload_folder(
                folder_path = save_directory,
                repo_id = repo_id,
                commit_message = "Upload GGUF and SentenceTransformer model",
            )
            print(f"Unsloth: Uploaded to https://huggingface.co/{repo_id}")
        except Exception as e:
            print(f"Unsloth: Upload failed: {e}")

    return result