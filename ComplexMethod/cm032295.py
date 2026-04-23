def test_update_different_params_dataset_success(get_auth):
    # create dataset
    res = create_dataset(get_auth, "test_create_dataset")
    assert res.get("code") == 0, f"{res.get('message')}"

    # list dataset
    page_number = 1
    dataset_list = []
    while True:
        res = list_dataset(get_auth, page_number)
        data = res.get("data").get("kbs")
        for item in data:
            dataset_id = item.get("id")
            dataset_list.append(dataset_id)
        if len(dataset_list) < page_number * 150:
            break
        page_number += 1

    print(f"found {len(dataset_list)} datasets")
    dataset_id = dataset_list[0]

    json_req = {"kb_id": dataset_id, "name": "test_update_dataset", "description": "test", "permission": "me",
                "parser_id": "presentation",
                "language": "spanish"}
    res = update_dataset(get_auth, json_req)
    assert res.get("code") == 0, f"{res.get('message')}"

    # delete dataset
    for dataset_id in dataset_list:
        res = rm_dataset(get_auth, dataset_id)
        assert res.get("code") == 0, f"{res.get('message')}"
    print(f"{len(dataset_list)} datasets are deleted")