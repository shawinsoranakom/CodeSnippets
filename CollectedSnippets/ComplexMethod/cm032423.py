def _prepare_dataset(
    client: HttpClient,
    args: argparse.Namespace,
    needs_dataset: bool,
    document_paths: List[str],
) -> Dict[str, Any]:
    created = {}
    dataset_ids = split_csv(args.dataset_ids) or []
    dataset_id = args.dataset_id
    dataset_payload = load_json_arg(args.dataset_payload, "dataset-payload") if args.dataset_payload else None

    if dataset_id:
        dataset_ids = [dataset_id]
    elif dataset_ids:
        dataset_id = dataset_ids[0]
    elif needs_dataset or document_paths:
        if not args.dataset_name and not (dataset_payload and dataset_payload.get("name")):
            raise DatasetError("Missing --dataset-name or dataset payload name")
        name = args.dataset_name or dataset_payload.get("name")
        data = create_dataset(client, name, dataset_payload)
        dataset_id = data.get("id")
        if not dataset_id:
            raise DatasetError("Dataset creation did not return id")
        dataset_ids = [dataset_id]
        created["Created Dataset ID"] = dataset_id
    return {
        "dataset_id": dataset_id,
        "dataset_ids": dataset_ids,
        "dataset_payload": dataset_payload,
        "created": created,
    }