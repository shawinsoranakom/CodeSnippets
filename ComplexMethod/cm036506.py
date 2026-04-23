def _mark_splits(
    test_settings: dict[str, VLMTestInfo],
    *,
    num_groups: int,
) -> dict[str, VLMTestInfo]:
    name_by_test_info_id = {id(v): k for k, v in test_settings.items()}
    test_infos_by_model = defaultdict[str, list[VLMTestInfo]](list)

    for info in test_settings.values():
        for model in info.models:
            test_infos_by_model[model].append(info)

    models = sorted(test_infos_by_model.keys())
    split_size = math.ceil(len(models) / num_groups)

    new_test_settings = dict[str, VLMTestInfo]()

    for i in range(num_groups):
        models_in_group = models[i * split_size : (i + 1) * split_size]

        for model in models_in_group:
            for info in test_infos_by_model[model]:
                new_marks = (info.marks or []) + [pytest.mark.split(group=i)]
                new_info = info._replace(marks=new_marks)
                new_test_settings[name_by_test_info_id[id(info)]] = new_info

    missing_keys = test_settings.keys() - new_test_settings.keys()
    assert not missing_keys, f"Missing keys: {missing_keys}"

    return new_test_settings