def upload_to_huggingface(
    model,
    save_directory,
    token,
    method,
    extra = "",
    file_location = None,
    old_username = None,
    private = None,
    create_config = True,
    datasets = None,
):
    save_directory, username = _determine_username(save_directory, old_username, token)

    from huggingface_hub import create_repo

    try:
        create_repo(
            repo_id = save_directory,
            token = token,
            repo_type = "model",
            exist_ok = False,
            private = private,
        )

        # Create model card
        from huggingface_hub import ModelCard

        content = MODEL_CARD.format(
            username = username,
            base_model = model.config._name_or_path,
            model_type = model.config.model_type,
            method = "",
            extra = extra,
        )
        card = ModelCard(content)
        if datasets:
            card.data.datasets = datasets
        card.push_to_hub(save_directory, token = token)
    except:
        # Repo already exists — update datasets metadata separately
        if datasets:
            try:
                from huggingface_hub import metadata_update

                metadata_update(
                    save_directory, {"datasets": datasets}, overwrite = True, token = token
                )
            except Exception as e:
                logger.warning_once(
                    f"Unsloth: Could not update datasets metadata for {save_directory}: {e}"
                )

    if file_location is not None:
        # Now upload file
        hf_api = HfApi(token = token)

        if "/" in file_location:
            uploaded_location = file_location[file_location.rfind("/") + 1 :]
        else:
            uploaded_location = file_location

        # find ftevent file from tensorboard and upload it
        import glob

        ftevent_files = glob.glob("*out.tfevents*", recursive = True)
        if len(ftevent_files) > 0:
            print(
                "Unsloth: Uploading tensorboard files... Please wait...",
                file_location + "*out.tfevents*",
            )
            for ftevent_file in ftevent_files:
                hf_api.upload_file(
                    path_or_fileobj = ftevent_file,
                    path_in_repo = ftevent_file.replace(file_location, ""),
                    repo_id = save_directory,
                    repo_type = "model",
                    commit_message = "(Trained with Unsloth)",
                )

        hf_api.upload_file(
            path_or_fileobj = file_location,
            path_in_repo = uploaded_location,
            repo_id = save_directory,
            repo_type = "model",
            commit_message = "(Trained with Unsloth)",
        )

        # We also upload a config.json file
        if create_config:
            import json

            with open("_temporary_unsloth_config.json", "w", encoding = "utf-8") as file:
                json.dump({"model_type": model.config.model_type}, file, indent = 4)
            hf_api.upload_file(
                path_or_fileobj = "_temporary_unsloth_config.json",
                path_in_repo = "config.json",
                repo_id = save_directory,
                repo_type = "model",
                commit_message = "(Trained with Unsloth)",
            )
            os.remove("_temporary_unsloth_config.json")
    return username