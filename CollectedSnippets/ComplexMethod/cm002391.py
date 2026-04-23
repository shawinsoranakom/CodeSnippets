def update_tiny_model_summary_file(report_path):
    with open(os.path.join(report_path, "tiny_model_summary.json")) as fp:
        new_data = json.load(fp)
    with open("tests/utils/tiny_model_summary.json") as fp:
        data = json.load(fp)
    for key, value in new_data.items():
        if key not in data:
            data[key] = value
        else:
            for attr in ["tokenizer_classes", "processor_classes", "model_classes"]:
                # we might get duplication here. We will remove them below when creating `updated_data`.
                data[key][attr].extend(value[attr])
            new_sha = value.get("sha", None)
            if new_sha is not None:
                data[key]["sha"] = new_sha

    updated_data = {}
    for key in sorted(data.keys()):
        updated_data[key] = {}
        for attr, value in data[key].items():
            # deduplication and sort
            updated_data[key][attr] = sorted(set(value)) if attr != "sha" else value

    with open(os.path.join(report_path, "updated_tiny_model_summary.json"), "w") as fp:
        json.dump(updated_data, fp, indent=4, ensure_ascii=False)