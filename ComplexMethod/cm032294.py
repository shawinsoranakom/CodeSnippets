def test_dataset_1k_dataset(get_auth):
    # create dataset
    for i in range(1000):
        res = create_dataset(get_auth, f"test_create_dataset_{i}")
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
    # delete dataset
    for dataset_id in dataset_list:
        res = rm_dataset(get_auth, dataset_id)
        assert res.get("code") == 0, f"{res.get('message')}"
    print(f"{len(dataset_list)} datasets are deleted")