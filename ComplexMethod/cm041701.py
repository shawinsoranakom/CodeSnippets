def get_dataset_list(dataset_names: list[str] | None, dataset_dir: str | dict) -> list["DatasetAttr"]:
    r"""Get the attributes of the datasets."""
    if dataset_names is None:
        dataset_names = []

    if isinstance(dataset_dir, dict):
        dataset_info = dataset_dir
    elif dataset_dir == "ONLINE":
        dataset_info = None
    else:
        if dataset_dir.startswith("REMOTE:"):
            config_path = hf_hub_download(repo_id=dataset_dir[7:], filename=DATA_CONFIG, repo_type="dataset")
        else:
            config_path = os.path.join(dataset_dir, DATA_CONFIG)

        try:
            with open(config_path) as f:
                dataset_info = json.load(f)
        except Exception as err:
            if len(dataset_names) != 0:
                raise ValueError(f"Cannot open {config_path} due to {str(err)}.")

            dataset_info = None

    dataset_list: list[DatasetAttr] = []
    for name in dataset_names:
        if dataset_info is None:  # dataset_dir is ONLINE
            load_from = "ms_hub" if use_modelscope() else "om_hub" if use_openmind() else "hf_hub"
            dataset_attr = DatasetAttr(load_from, dataset_name=name)
            dataset_list.append(dataset_attr)
            continue

        if name not in dataset_info:
            raise ValueError(f"Undefined dataset {name} in {DATA_CONFIG}.")

        has_hf_url = "hf_hub_url" in dataset_info[name]
        has_ms_url = "ms_hub_url" in dataset_info[name]
        has_om_url = "om_hub_url" in dataset_info[name]

        if has_hf_url or has_ms_url or has_om_url:
            if has_ms_url and (use_modelscope() or not has_hf_url):
                dataset_attr = DatasetAttr("ms_hub", dataset_name=dataset_info[name]["ms_hub_url"])
            elif has_om_url and (use_openmind() or not has_hf_url):
                dataset_attr = DatasetAttr("om_hub", dataset_name=dataset_info[name]["om_hub_url"])
            else:
                dataset_attr = DatasetAttr("hf_hub", dataset_name=dataset_info[name]["hf_hub_url"])
        elif "script_url" in dataset_info[name]:
            dataset_attr = DatasetAttr("script", dataset_name=dataset_info[name]["script_url"])
        elif "cloud_file_name" in dataset_info[name]:
            dataset_attr = DatasetAttr("cloud_file", dataset_name=dataset_info[name]["cloud_file_name"])
        else:
            dataset_attr = DatasetAttr("file", dataset_name=dataset_info[name]["file_name"])

        dataset_attr.join(dataset_info[name])
        dataset_list.append(dataset_attr)

    return dataset_list