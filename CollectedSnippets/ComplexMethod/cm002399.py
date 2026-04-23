def get_list_of_models_to_deprecate(
    thresh_num_downloads=5_000,
    thresh_date=None,
    use_cache=False,
    save_model_info=False,
    max_num_models=-1,
):
    if thresh_date is None:
        thresh_date = datetime.now(timezone.utc).replace(year=datetime.now(timezone.utc).year - 1)
    else:
        thresh_date = datetime.strptime(thresh_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)

    models_dir = PATH_TO_REPO / "src/transformers/models"
    model_paths = get_list_of_repo_model_paths(models_dir=models_dir)

    if use_cache and os.path.exists("models_info.json"):
        with open("models_info.json", "r") as f:
            models_info = json.load(f)
        # Convert datetimes back to datetime objects
        for model, info in models_info.items():
            info["first_commit_datetime"] = datetime.fromisoformat(info["first_commit_datetime"])

    else:
        print("Building a dictionary of basic model info...")
        models_info = defaultdict(dict)
        for i, model_path in enumerate(tqdm(sorted(model_paths))):
            if max_num_models != -1 and i > max_num_models:
                break
            model = model_path.split("/")[-2]
            if model in models_info:
                continue
            commits = repo.git.log("--diff-filter=A", "--", model_path).split("\n")
            commit_hash = _extract_commit_hash(commits)
            commit_obj = repo.commit(commit_hash)
            committed_datetime = commit_obj.committed_datetime
            models_info[model]["commit_hash"] = commit_hash
            models_info[model]["first_commit_datetime"] = committed_datetime
            models_info[model]["model_path"] = model_path
            models_info[model]["downloads"] = 0
            models_info[model]["tags"] = [model]

        # The keys in the dictionary above are the model folder names. In some cases, the model tag on the hub does not
        # match the model folder name. We replace the key and append the expected tag.
        for folder_name, expected_tag in MODEL_FOLDER_NAME_TO_TAG_MAPPING.items():
            if folder_name in models_info:
                models_info[expected_tag] = models_info[folder_name]
                models_info[expected_tag]["tags"] = [expected_tag]
                del models_info[folder_name]

        # Some models have multiple tags on the hub. We add the expected tag to the list of tags.
        for model_name, extra_tags in EXTRA_TAGS_MAPPING.items():
            if model_name in models_info:
                models_info[model_name]["tags"].extend(extra_tags)

        # Sanity check for the case with all models: the model tags must match the keys in the CONFIG_MAPPING_NAMES
        # (= actual model tags on the hub)
        if max_num_models == -1:
            all_model_tags = set()
            for model_name in models_info:
                all_model_tags.update(models_info[model_name]["tags"])

            non_deprecated_model_tags = (
                set(CONFIG_MAPPING_NAMES.keys()) - set(DEPRECATED_MODELS_TAGS) - set(DEPRECATED_MODELS)
            )
            if all_model_tags != non_deprecated_model_tags:
                raise ValueError(
                    "The tags of the `models_info` dictionary must match the keys in the `CONFIG_MAPPING_NAMES`!"
                    "\nMissing tags in `model_info`: "
                    + str(sorted(non_deprecated_model_tags - all_model_tags))
                    + "\nExtra tags in `model_info`: "
                    + str(sorted(all_model_tags - non_deprecated_model_tags))
                    + "\n\nYou need to update one or more of the following: `CONFIG_MAPPING_NAMES`, "
                    "`EXTRA_TAGS_MAPPING` or `DEPRECATED_MODELS_TAGS`."
                )

        # Filter out models which were added less than a year ago
        models_info = {
            model: info for model, info in models_info.items() if info["first_commit_datetime"] < thresh_date
        }

        # We make successive calls to the hub, filtering based on the model tags
        print("Making calls to the hub to find models below the threshold number of downloads...")
        num_models = len(models_info)
        for i, (model, model_info) in enumerate(models_info.items()):
            print(f"{i + 1}/{num_models}: getting hub downloads for model='{model}' (tags={model_info['tags']})")
            for model_tag in model_info["tags"]:
                if model_info["downloads"] > thresh_num_downloads:
                    break
                model_list = HubModelLister(tags=model_tag)
                for hub_model in model_list:
                    if hub_model.private:
                        continue
                    model_info["downloads"] += hub_model.downloads
                    # No need to make further hub calls, it's above the set threshold
                    if model_info["downloads"] > thresh_num_downloads:
                        break

    if save_model_info and not (use_cache and os.path.exists("models_info.json")):
        # Make datetimes serializable
        for model, info in models_info.items():
            info["first_commit_datetime"] = info["first_commit_datetime"].isoformat()
        with open("models_info.json", "w") as f:
            json.dump(models_info, f, indent=4)

    print("\nFinding models to deprecate:")
    n_models_to_deprecate = 0
    models_to_deprecate = {}
    for model, info in models_info.items():
        n_downloads = info["downloads"]
        if n_downloads < thresh_num_downloads:
            n_models_to_deprecate += 1
            models_to_deprecate[model] = info
            print(f"\nModel: {model}")
            print(f"Downloads: {n_downloads}")
            print(f"Date: {info['first_commit_datetime']}")

    # sort models to deprecate by downloads (lowest downloads first)
    models_to_deprecate = sorted(models_to_deprecate.items(), key=lambda x: x[1]["downloads"])

    print("\nModels to deprecate: ", "\n" + "\n".join([model[0] for model in models_to_deprecate]))
    print(f"\nNumber of models to deprecate: {n_models_to_deprecate}")
    print("Before deprecating make sure to verify the models, including if they're used as a module in other models.")