def _validate_dataset_ids(dataset_ids, tenant_id):
    if dataset_ids is None:
        return []
    if not isinstance(dataset_ids, list):
        return "`dataset_ids` should be a list."

    normalized_ids = [dataset_id for dataset_id in dataset_ids if dataset_id]
    kbs = []
    for dataset_id in normalized_ids:
        if not KnowledgebaseService.accessible(kb_id=dataset_id, user_id=tenant_id):
            return f"You don't own the dataset {dataset_id}"
        matches = KnowledgebaseService.query(id=dataset_id)
        if not matches:
            return f"You don't own the dataset {dataset_id}"
        kb = matches[0]
        if kb.chunk_num == 0:
            return f"The dataset {dataset_id} doesn't own parsed file"
        kbs.append(kb)

    embd_ids = [TenantLLMService.split_model_name_and_factory(kb.embd_id)[0] for kb in kbs]
    if len(set(embd_ids)) > 1:
        return f'Datasets use different embedding models: {[kb.embd_id for kb in kbs]}'

    return normalized_ids