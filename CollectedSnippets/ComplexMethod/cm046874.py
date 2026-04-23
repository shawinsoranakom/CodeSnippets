def unsloth_save_model(
    model,
    tokenizer,
    save_directory: Union[str, os.PathLike],
    save_method: str = "lora",  # ["lora", "merged_16bit", "merged_4bit"]
    push_to_hub: bool = False,
    token: Optional[Union[str, bool]] = None,
    is_main_process: bool = True,
    state_dict: Optional[dict] = None,
    save_function: Callable = torch.save,
    max_shard_size: Union[int, str] = "5GB",
    safe_serialization: bool = True,
    variant: Optional[str] = None,
    save_peft_format: bool = True,
    # Push to hub
    use_temp_dir: Optional[bool] = None,
    commit_message: Optional[str] = "Trained with Unsloth",
    private: Optional[bool] = None,
    create_pr: bool = False,
    revision: str = None,
    commit_description: str = "Upload model trained with Unsloth 2x faster",
    tags: List[str] = None,
    # Our functions
    temporary_location: str = "_unsloth_temporary_saved_buffers",
    maximum_memory_usage: float = 0.9,
    datasets: Optional[List[str]] = None,
):
    if isinstance(tokenizer, (PreTrainedTokenizerBase, ProcessorMixin)):
        tokenizer = patch_saving_functions(tokenizer)

    if token is None:
        token = get_token()

    if commit_message is None:
        commit_message = ""
    if "Unsloth" not in commit_message:
        commit_message += " (Trained with Unsloth)"
    commit_message = commit_message.lstrip()

    if commit_description is None:
        commit_description = "Upload model trained with Unsloth 2x faster"
    elif "Unsloth 2x faster" not in commit_description:
        commit_description += " (Trained with Unsloth 2x faster)"

    if save_method == "merged_4bit":
        raise RuntimeError(
            "Unsloth: Merging into 4bit will cause your model to lose accuracy if you plan\n"
            "to merge to GGUF or others later on. I suggest you to do this as a final step\n"
            "if you're planning to do multiple saves.\n"
            "If you are certain, change `save_method` to `merged_4bit_forced`."
        )
    elif save_method == "merged_4bit_forced":
        save_method = "merged_4bit"

    save_pretrained_settings = dict(locals())
    for deletion in (
        "model",
        "tokenizer",
        "save_method",
        "temporary_location",
        "maximum_memory_usage",
        "datasets",
    ):
        del save_pretrained_settings[deletion]

    # First check for a token!
    if push_to_hub:
        from huggingface_hub import whoami

        try:
            username = whoami(token = token)["name"]
        except:
            raise RuntimeError(
                "Unsloth: Please supply a token!\n"
                "Go to https://huggingface.co/settings/tokens"
            )

    assert maximum_memory_usage > 0 and maximum_memory_usage <= 0.95

    # Clean memory up first
    for _ in range(3):
        torch.cuda.empty_cache()
        gc.collect()

    save_method = save_method.lower().replace(" ", "_")
    if (
        save_method != "lora"
        and save_method != "merged_16bit"
        and save_method != "merged_4bit"
    ):
        raise RuntimeError(
            "Unsloth: You must select one of 3 options when saving models:\n"
            '"lora"         ==> This is the fastest and easiet. Just saves LoRA modules.\n'
            '"merged_16bit" ==> This merges LoRA weights and saves to float16. Needed for llama.cpp / GGUF.\n'
            '"merged_4bit"  ==> This merges LoRA weights and saves to 4bit. Useful for DPO / inference.'
        )

    if save_method == "merged_4bit":
        print("Unsloth: Merging 4bit and LoRA weights to 4bit...")
        print("This might take 5 minutes...")

        # Counteract no LoRA adapters!
        if hasattr(model, "merge_and_unload"):
            model = model.merge_and_unload()
        print("Done.")

    if tags is not None:
        assert isinstance(tags, (list, tuple))
        tags = list(tags) + [
            "unsloth",
        ]
    else:
        tags = [
            "unsloth",
        ]
    save_pretrained_settings["tags"] = tags

    if ((save_method == "lora") or (save_method == "merged_4bit")) and push_to_hub:
        if token is None:
            raise RuntimeError(
                "Unsloth: Pushing to HF requires a token. Pass `token = 'hf_....'`\n"
                "Go to https://huggingface.co/settings/tokens."
            )

        if save_method == "lora":
            print("Unsloth: Saving LoRA adapters. Please wait...")
        elif save_method == "merged_4bit":
            print("Unsloth: Saving 4bit Bitsandbytes model. Please wait...")

        # Update model tag
        _ = upload_to_huggingface(
            model,
            save_directory,
            token,
            "finetuned",
            "trl",
            file_location = None,
            old_username = None,
            private = private,
            datasets = datasets,
        )

        getattr(model, "original_push_to_hub", model.push_to_hub)(
            repo_id = save_directory,
            use_temp_dir = use_temp_dir,
            commit_message = commit_message,
            private = private,
            token = token,
            max_shard_size = max_shard_size,
            create_pr = create_pr,
            safe_serialization = safe_serialization,
            revision = revision,
            commit_description = commit_description,
            tags = tags,
        )
        if tokenizer is not None:
            # Set padding side to left for inference
            _tokenizer = (
                tokenizer.tokenizer if hasattr(tokenizer, "tokenizer") else tokenizer
            )
            old_padding_side = _tokenizer.padding_side
            _tokenizer.padding_side = "left"

            getattr(tokenizer, "original_push_to_hub", tokenizer.push_to_hub)(
                repo_id = save_directory,
                use_temp_dir = use_temp_dir,
                commit_message = commit_message,
                private = private,
                token = token,
                max_shard_size = max_shard_size,
                create_pr = create_pr,
                safe_serialization = safe_serialization,
                revision = revision,
                commit_description = commit_description,
                tags = tags,
            )

            # Revert back padding side
            _tokenizer.padding_side = old_padding_side

        if hasattr(model, "config"):
            print(
                f"Saved {save_method} model to https://huggingface.co/" + save_directory
            )
        return save_directory, None

    # Tokenizer has different saving arguments
    tokenizer_save_settings = {
        "save_directory": save_pretrained_settings["save_directory"],
        "legacy_format": None,
        "filename_prefix": None,
        "push_to_hub": save_pretrained_settings["push_to_hub"],
        "private": save_pretrained_settings["private"],
        "token": save_pretrained_settings["token"],
    }

    # Check if PEFT Model or not - if yes, 3 levels. If not 2 levels.
    from peft import PeftModelForCausalLM

    if isinstance(model, PeftModelForCausalLM):
        internal_model = model.model
    else:
        internal_model = model

    # Cannot be converted properly!
    if (
        (save_method == "merged_4bit")
        or (save_method == "lora")
        or (not hasattr(model, "model") or not hasattr(internal_model.model, "layers"))
    ):
        # Do general saving
        # Edit save_pretrained_settings
        # [TODO] _create_repo has errors due to **kwargs getting accepted
        # commit_description does not seem to work?
        what_to_delete = (
            (
                "use_temp_dir",
                "commit_message",
                "create_pr",
                "revision",
                "commit_description",
                "tags",
            )
            if save_pretrained_settings["push_to_hub"] is False
            else (
                "use_temp_dir",
                "create_pr",
                "revision",
                "tags",
                "commit_description",
            )
        )
        for deletion in what_to_delete:
            del save_pretrained_settings[deletion]
        if hasattr(model, "add_model_tags"):
            model.add_model_tags(
                [
                    "unsloth",
                ]
            )

        # Update model tag
        if push_to_hub:
            _ = upload_to_huggingface(
                model,
                save_pretrained_settings["save_directory"],
                token,
                "finetuned",
                "trl",
                file_location = None,
                old_username = None,
                private = private,
                datasets = datasets,
            )

        if tokenizer is not None:
            print("Unsloth: Saving tokenizer...", end = "")

            # Set padding side to left for inference
            _tokenizer = (
                tokenizer.tokenizer if hasattr(tokenizer, "tokenizer") else tokenizer
            )
            old_padding_side = _tokenizer.padding_side
            _tokenizer.padding_side = "left"

            tokenizer.save_pretrained(**tokenizer_save_settings)

            # Revert back padding side
            _tokenizer.padding_side = old_padding_side

            print(" Done.")
        else:
            print()

        print("Unsloth: Saving model...", end = "")
        if save_method != "lora":
            print(" This might take 10 minutes for Llama-7b...", end = "")

        # [TODO] Is this correct?
        if save_method == "lora":
            save_pretrained_settings["selected_adapters"] = None

        model.save_pretrained(**save_pretrained_settings)

        if push_to_hub and hasattr(model, "config"):
            print(
                "Saved to https://huggingface.co/"
                + save_pretrained_settings["save_directory"]
            )

        print(" Done.")
        return save_directory, None

    # If push_to_hub, we must remove the .../ part of a repo
    username = None
    if push_to_hub and "/" in save_directory:
        # +1 solves absolute path issues
        new_save_directory = save_directory
        username = new_save_directory[: new_save_directory.find("/")]
        new_save_directory = new_save_directory[new_save_directory.find("/") + 1 :]
        if IS_KAGGLE_ENVIRONMENT:
            new_save_directory = os.path.join(
                KAGGLE_TMP, new_save_directory[new_save_directory.find("/") + 1 :]
            )
            logger.warning_once(
                "Unsloth: You are pushing to hub in Kaggle environment.\n"
                f"To save memory, we shall move {save_directory} to {new_save_directory}"
            )
        else:
            logger.warning_once(
                f"Unsloth: You are pushing to hub, but you passed your HF username = {username}.\n"
                f"We shall truncate {save_directory} to {new_save_directory}"
            )

        save_pretrained_settings["save_directory"] = new_save_directory
        tokenizer_save_settings["save_directory"] = new_save_directory
        save_directory = new_save_directory

    print("Unsloth: Merging 4bit and LoRA weights to 16bit...")

    # Determine max RAM usage minus sharding
    max_ram = psutil.virtual_memory().available
    sharded_ram_usage = 5 * 1024 * 1024 * 1024
    if type(max_shard_size) is str:
        gb_found = re.match(
            r"([0-9]{1,})[\s]{0,}GB", max_shard_size, flags = re.IGNORECASE
        )
        mb_found = re.match(
            r"([0-9]{1,})[\s]{0,}MB", max_shard_size, flags = re.IGNORECASE
        )
        if gb_found:
            sharded_ram_usage = int(gb_found.group(1)) * 1024 * 1024 * 1024
        elif mb_found:
            sharded_ram_usage = int(mb_found.group(1)) * 1024 * 1024
    elif type(max_shard_size) is int:
        sharded_ram_usage = max_shard_size

    # Switch to our fast saving modules if it's a slow PC!
    n_cpus = psutil.cpu_count(logical = False)
    if n_cpus is None:
        n_cpus = psutil.cpu_count()
    if n_cpus is None:
        n_cpus = 1

    if safe_serialization is None:
        safe_serialization = True
        save_pretrained_settings["safe_serialization"] = safe_serialization

    elif safe_serialization and (n_cpus <= 2):
        logger.warning_once(
            f"Unsloth: You have {n_cpus} CPUs. Using `safe_serialization` is 10x slower.\n"
            f"We shall switch to Pytorch saving, which might take 3 minutes and not 30 minutes.\n"
            f"To force `safe_serialization`, set it to `None` instead.",
        )
        safe_serialization = False
        save_function = fast_save_pickle
        save_pretrained_settings["safe_serialization"] = safe_serialization
        save_pretrained_settings["save_function"] = save_function

    # Only safe_serialization uses more RAM
    if safe_serialization:
        max_ram -= sharded_ram_usage
    else:
        max_ram -= sharded_ram_usage * 0.25  # Uses much less

    max_ram = int(max(0, max_ram) * maximum_memory_usage)
    print(
        f"Unsloth: Will use up to "
        f"{round(max_ram/1024/1024/1024, 2)} out of "
        f"{round(psutil.virtual_memory().total/1024/1024/1024, 2)} RAM for saving."
    )

    # Move temporary_location to /tmp in Kaggle
    if IS_KAGGLE_ENVIRONMENT:
        temporary_location = os.path.join(KAGGLE_TMP, temporary_location)

    # Max directory for disk saving
    if not os.path.exists(temporary_location):
        os.makedirs(temporary_location)

    # Check if Kaggle or Colab, since only 20GB of Disk space allowed.
    if IS_KAGGLE_ENVIRONMENT or IS_COLAB_ENVIRONMENT:
        # We free up 4GB of space
        logger.warning_once(
            "Unsloth: Kaggle/Colab has limited disk space. We need to delete the downloaded\n"
            "model which will save 4-16GB of disk space, allowing you to save on Kaggle/Colab."
        )
        _free_cached_model(internal_model)

    # HF also uses a OrderedDict
    from collections import OrderedDict

    state_dict = OrderedDict()

    torch_dtype = dtype_from_config(internal_model.config)
    if type(torch_dtype) is str:
        if torch_dtype == "float16":
            torch_dtype = torch.float16
        elif torch_dtype == "bfloat16":
            torch_dtype = torch.bfloat16

    # Check modules to save float32 dtype
    state_dict["model.embed_tokens.weight"] = (
        internal_model.model.embed_tokens.weight.data.to(torch_dtype)
    )

    max_vram = int(
        torch.cuda.get_device_properties(0).total_memory * maximum_memory_usage
    )

    print("Unsloth: Saving model... This might take 5 minutes ...")

    from tqdm import tqdm as ProgressBar

    for j, layer in enumerate(ProgressBar(internal_model.model.layers)):
        for item in LLAMA_WEIGHTS:
            proj = eval(f"layer.{item}")
            name = f"model.layers.{j}.{item}.weight"
            W, bias = _merge_lora(proj, name)

            # Bias term
            if bias is not None:
                state_dict[f"model.layers.{j}.{item}.bias"] = bias

            if (torch.cuda.memory_allocated() + W.nbytes) < max_vram:
                # Save to GPU memory
                state_dict[name] = W
            # [TODO] Saving to RAM seems to leak memory???
            # elif (max_ram - W.nbytes) > 0:
            #     # Save to CPU memory
            #     logger.warning_once(f"We will save to RAM and not VRAM now.")
            #     state_dict[name] = W.to("cpu", non_blocking = True, copy = True)
            #     max_ram = max(max_ram - W.nbytes, 0)
            else:
                # Save to Disk
                logger.warning_once("\nWe will save to Disk and not RAM now.")
                filename = os.path.join(temporary_location, f"{name}.pt")
                torch.save(
                    W,
                    filename,
                    pickle_module = pickle,
                    pickle_protocol = pickle.HIGHEST_PROTOCOL,
                )
                # weights_only = True weirdly fails?
                state_dict[name] = torch.load(
                    filename, map_location = "cpu", mmap = True, weights_only = False
                )
        for item in LLAMA_LAYERNORMS:
            try:
                # Skip for Gemma 2
                state_dict[f"model.layers.{j}.{item}.weight"] = eval(
                    f"layer.{item}.weight.data"
                )
            except:
                continue

    state_dict["model.norm.weight"] = internal_model.model.norm.weight.data
    # Check for modules_to_save float32 dtype

    # Check for tied weights
    if (
        internal_model.model.embed_tokens.weight.data_ptr()
        != internal_model.lm_head.weight.data_ptr()
    ):
        state_dict["lm_head.weight"] = internal_model.lm_head.weight.data.to(
            torch_dtype
        )

    # All tensors MUST be type torch.Tensor and not torch.nn.parameter.Parameter
    for key, value in state_dict.items():
        if hasattr(value, "data"):
            state_dict[key] = value = value.data
        if type(value) is not torch.Tensor:
            logger.warning_once(f"Unsloth: {key} is not a Tensor but a {type(value)}.")

    # Edit save_pretrained_settings
    # [TODO] _create_repo has errors due to **kwargs getting accepted
    save_pretrained_settings["state_dict"] = state_dict

    # commit_description does not seem to work?
    what_to_delete = (
        (
            "use_temp_dir",
            "commit_message",
            "create_pr",
            "revision",
            "commit_description",
            "tags",
        )
        if not push_to_hub
        else (
            "use_temp_dir",
            "create_pr",
            "revision",
            "tags",
            "commit_description",
        )
    )
    for deletion in what_to_delete:
        del save_pretrained_settings[deletion]
    if hasattr(model, "add_model_tags"):
        model.add_model_tags(
            [
                "unsloth",
            ]
        )

    # Update model tag
    if push_to_hub:
        _ = upload_to_huggingface(
            model,
            save_pretrained_settings["save_directory"],
            token,
            "finetuned",
            "trl",
            file_location = None,
            old_username = username,
            private = private,
            datasets = datasets,
        )

    # First check if we're pushing to an organization!
    save_directory = save_pretrained_settings["save_directory"]

    if save_pretrained_settings["push_to_hub"]:
        new_save_directory, new_username = _determine_username(
            save_directory, username, token
        )

        if token is not None:
            from huggingface_hub import whoami

            actual_username = whoami(token = token)["name"]
        else:
            actual_username = username

    # Check if pushing to an organization
    if save_pretrained_settings["push_to_hub"] and (username != actual_username):
        print(f"Unsloth: Saving to organization with address {new_save_directory}")
        # We upload everything at the end!
        tokenizer_save_settings["push_to_hub"] = False
        tokenizer_save_settings["save_directory"] = new_save_directory

    # Save tokenizer
    if tokenizer is not None:
        print("Unsloth: Saving tokenizer...", end = "")

        # Set padding side to left for inference
        _tokenizer = (
            tokenizer.tokenizer if hasattr(tokenizer, "tokenizer") else tokenizer
        )
        old_padding_side = _tokenizer.padding_side
        _tokenizer.padding_side = "left"

        tokenizer.save_pretrained(**tokenizer_save_settings)

        # Revert back padding side
        _tokenizer.padding_side = old_padding_side

        print(" Done.")
    else:
        print()

    # Since merged, edit quantization_config
    old_config = model.config
    new_config = model.config.to_dict()
    if "quantization_config" in new_config:
        del new_config["quantization_config"]
    original_model = model
    new_config = type(model.config).from_dict(new_config)
    while hasattr(original_model, "model"):
        original_model = original_model.model
        original_model.config = new_config
    model.config = new_config

    # Save!
    # [TODO] --> is this correct?
    # save_pretrained_settings["selected_adapters"] = None

    # Check if pushing to an organization
    if save_pretrained_settings["push_to_hub"] and (username != actual_username):
        print(f"Unsloth: Saving to organization with address {new_save_directory}")
        # Pushing to organization!
        # Sadly .save_pretrained doesn't work :(
        # We first save it via .save_pretrained, then upload manually!
        save_pretrained_settings["save_directory"] = new_save_directory
        save_pretrained_settings["push_to_hub"] = False
        internal_model.save_pretrained(**save_pretrained_settings)

        # Now manually go through each file and upload them manually!
        filenames = os.listdir(new_save_directory)

        hf_api = HfApi(token = save_pretrained_settings["token"])

        print("Unsloth: Uploading all files... Please wait...")
        hf_api.upload_folder(
            folder_path = new_save_directory,
            path_in_repo = ".",
            repo_id = new_save_directory,
            repo_type = "model",
            commit_message = "(Trained with Unsloth)",
            ignore_patterns = "*.md",
        )
    else:
        internal_model.save_pretrained(**save_pretrained_settings)

    # Revert config back
    original_model = model
    while hasattr(original_model, "model"):
        original_model = original_model.model
        original_model.config = old_config
    model.config = old_config
    print("Done.")

    if push_to_hub and hasattr(model, "config"):
        print(
            f"Saved merged model to https://huggingface.co/{username}/{save_directory.lstrip('/').split('/')[-1]}"
        )

    save_pretrained_settings["state_dict"] = None

    for j, (key, value) in enumerate(state_dict.items()):
        state_dict[key] = None
        if j % 10 == 0:
            torch.cuda.empty_cache()
            gc.collect()
    state_dict = None
    del state_dict
    torch.cuda.empty_cache()
    gc.collect()

    # Remove temporary location
    import shutil

    shutil.rmtree(temporary_location, ignore_errors = True)

    for _ in range(3):
        torch.cuda.empty_cache()
        gc.collect()
    return save_directory, username