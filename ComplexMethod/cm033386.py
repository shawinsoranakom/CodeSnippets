def run_graphrag(dataset_id: str, tenant_id: str):
    """
    Run GraphRAG for a dataset.

    :param dataset_id: dataset ID
    :param tenant_id: tenant ID
    :return: (success, result) or (success, error_message)
    """
    if not dataset_id:
        return False, 'Lack of "Dataset ID"'
    if not KnowledgebaseService.accessible(dataset_id, tenant_id):
        return False, "No authorization."

    ok, kb = KnowledgebaseService.get_by_id(dataset_id)
    if not ok:
        return False, "Invalid Dataset ID"

    task_id = kb.graphrag_task_id
    if task_id:
        ok, task = TaskService.get_by_id(task_id)
        if not ok:
            logging.warning(f"A valid GraphRAG task id is expected for Dataset {dataset_id}")

        if task and task.progress not in [-1, 1]:
            return False, f"Task {task_id} in progress with status {task.progress}. A Graph Task is already running."

    documents, _ = DocumentService.get_by_kb_id(
        kb_id=dataset_id,
        page_number=0,
        items_per_page=0,
        orderby="create_time",
        desc=False,
        keywords="",
        run_status=[],
        types=[],
        suffix=[],
    )
    if not documents:
        return False, f"No documents in Dataset {dataset_id}"

    sample_document = documents[0]
    document_ids = [document["id"] for document in documents]

    task_id = queue_raptor_o_graphrag_tasks(sample_doc=sample_document, ty="graphrag", priority=0, fake_doc_id=GRAPH_RAPTOR_FAKE_DOC_ID, doc_ids=list(document_ids))

    if not KnowledgebaseService.update_by_id(kb.id, {"graphrag_task_id": task_id}):
        logging.warning(f"Cannot save graphrag_task_id for Dataset {dataset_id}")

    return True, {"graphrag_task_id": task_id}