def wait_for_parse_done(
    client: HttpClient,
    dataset_id: str,
    document_ids: Optional[List[str]],
    timeout: float,
    interval: float,
) -> None:
    import time

    start = time.monotonic()
    while True:
        data = list_documents(client, dataset_id)
        docs = data.get("docs", [])
        target_ids = set(document_ids or [])
        all_done = True
        for doc in docs:
            if target_ids and doc.get("id") not in target_ids:
                continue
            if doc.get("run") != "DONE":
                all_done = False
                break
        if all_done:
            return
        if time.monotonic() - start > timeout:
            raise DatasetError("Document parsing timeout")
        time.sleep(max(interval, 0.1))