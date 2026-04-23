async def run_mindmap():
    req = await get_request_json()

    kb_id = req.get("kb_id", "")
    if not kb_id:
        return get_error_data_result(message='Lack of "KB ID"')

    ok, kb = KnowledgebaseService.get_by_id(kb_id)
    if not ok:
        return get_error_data_result(message="Invalid Knowledgebase ID")

    task_id = kb.mindmap_task_id
    if task_id:
        ok, task = TaskService.get_by_id(task_id)
        if not ok:
            logging.warning(f"A valid Mindmap task id is expected for kb {kb_id}")

        if task and task.progress not in [-1, 1]:
            return get_error_data_result(message=f"Task {task_id} in progress with status {task.progress}. A Mindmap Task is already running.")

    documents, _ = DocumentService.get_by_kb_id(
        kb_id=kb_id,
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
        return get_error_data_result(message=f"No documents in Knowledgebase {kb_id}")

    sample_document = documents[0]
    document_ids = [document["id"] for document in documents]

    task_id = queue_raptor_o_graphrag_tasks(sample_doc=sample_document, ty="mindmap", priority=0, fake_doc_id=GRAPH_RAPTOR_FAKE_DOC_ID, doc_ids=list(document_ids))

    if not KnowledgebaseService.update_by_id(kb.id, {"mindmap_task_id": task_id}):
        logging.warning(f"Cannot save mindmap_task_id for kb {kb_id}")

    return get_json_result(data={"mindmap_task_id": task_id})