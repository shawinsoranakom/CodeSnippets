def test_parse_txt_document(get_auth):
    # create dataset
    res = create_dataset(get_auth, "test_parse_txt_document")
    assert res.get("code") == 0, f"{res.get('message')}"

    # list dataset
    page_number = 1
    dataset_list = []
    dataset_id = None
    while True:
        res = list_dataset(get_auth, page_number)
        data = res.get("data").get("kbs")
        for item in data:
            dataset_id = item.get("id")
            dataset_list.append(dataset_id)
        if len(dataset_list) < page_number * 150:
            break
        page_number += 1

    filename = 'ragflow_test.txt'
    res = upload_file(get_auth, dataset_id, f"../test_sdk_api/test_data/{filename}")
    assert res.get("code") == 0, f"{res.get('message')}"

    res = list_document(get_auth, dataset_id)

    doc_id_list = []
    for doc in res['data']['docs']:
        doc_id_list.append(doc['id'])

    res = get_docs_info(get_auth, dataset_id, doc_ids=doc_id_list)
    print(doc_id_list)
    doc_count = len(doc_id_list)
    res = parse_docs(get_auth, doc_id_list)

    start_ts = timer()
    while True:
        res = get_docs_info(get_auth, dataset_id, doc_ids=doc_id_list)
        finished_count = 0
        for doc_info in res['data']:
            if doc_info['progress'] == 1:
                finished_count += 1
        if finished_count == doc_count:
            break
        sleep(1)
    print('time cost {:.1f}s'.format(timer() - start_ts))

    # delete dataset
    for dataset_id in dataset_list:
        res = rm_dataset(get_auth, dataset_id)
        assert res.get("code") == 0, f"{res.get('message')}"
    print(f"{len(dataset_list)} datasets are deleted")