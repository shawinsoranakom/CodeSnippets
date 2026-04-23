def delete_kb_task():
    kb_id = request.args.get("kb_id", "")
    if not kb_id:
        return get_error_data_result(message='Lack of "KB ID"')
    ok, kb = KnowledgebaseService.get_by_id(kb_id)
    if not ok:
        return get_json_result(data=True)

    pipeline_task_type = request.args.get("pipeline_task_type", "")
    if not pipeline_task_type or pipeline_task_type not in [PipelineTaskType.GRAPH_RAG, PipelineTaskType.RAPTOR, PipelineTaskType.MINDMAP]:
        return get_error_data_result(message="Invalid task type")

    def cancel_task(task_id):
        REDIS_CONN.set(f"{task_id}-cancel", "x")

    kb_task_id_field: str = ""
    kb_task_finish_at: str = ""
    match pipeline_task_type:
        case PipelineTaskType.GRAPH_RAG:
            kb_task_id_field = "graphrag_task_id"
            task_id = kb.graphrag_task_id
            kb_task_finish_at = "graphrag_task_finish_at"
            cancel_task(task_id)
            settings.docStoreConn.delete({"knowledge_graph_kwd": ["graph", "subgraph", "entity", "relation"]}, search.index_name(kb.tenant_id), kb_id)
        case PipelineTaskType.RAPTOR:
            kb_task_id_field = "raptor_task_id"
            task_id = kb.raptor_task_id
            kb_task_finish_at = "raptor_task_finish_at"
            cancel_task(task_id)
            settings.docStoreConn.delete({"raptor_kwd": ["raptor"]}, search.index_name(kb.tenant_id), kb_id)
        case PipelineTaskType.MINDMAP:
            kb_task_id_field = "mindmap_task_id"
            task_id = kb.mindmap_task_id
            kb_task_finish_at = "mindmap_task_finish_at"
            cancel_task(task_id)
        case _:
            return get_error_data_result(message="Internal Error: Invalid task type")


    ok = KnowledgebaseService.update_by_id(kb_id, {kb_task_id_field: "", kb_task_finish_at: None})
    if not ok:
        return server_error_response(f"Internal error: cannot delete task {pipeline_task_type}")

    return get_json_result(data=True)