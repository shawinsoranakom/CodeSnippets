def detail():
    kb_id = request.args["kb_id"]
    try:
        tenants = UserTenantService.query(user_id=current_user.id)
        for tenant in tenants:
            if KnowledgebaseService.query(
                    tenant_id=tenant.tenant_id, id=kb_id):
                break
        else:
            return get_json_result(
                data=False, message='Only owner of dataset authorized for this operation.',
                code=RetCode.OPERATING_ERROR)
        kb = KnowledgebaseService.get_detail(kb_id)
        if not kb:
            return get_data_error_result(
                message="Can't find this dataset!")
        kb["size"] = DocumentService.get_total_size_by_kb_id(kb_id=kb["id"],keywords="", run_status=[], types=[])
        kb["connectors"] = Connector2KbService.list_connectors(kb_id)
        if kb["parser_config"].get("metadata"):
            kb["parser_config"]["metadata"] = turn2jsonschema(kb["parser_config"]["metadata"])

        for key in ["graphrag_task_finish_at", "raptor_task_finish_at", "mindmap_task_finish_at"]:
            if finish_at := kb.get(key):
                kb[key] = finish_at.strftime("%Y-%m-%d %H:%M:%S")
        return get_json_result(data=kb)
    except Exception as e:
        return server_error_response(e)