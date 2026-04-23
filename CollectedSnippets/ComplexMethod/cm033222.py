def fix_empty_tenant_model_id():
    # knowledgebase
    empty_tenant_embd_id_kbs = KnowledgebaseService.get_null_tenant_embd_id_row()
    if empty_tenant_embd_id_kbs:
        logging.info(f"Found {len(empty_tenant_embd_id_kbs)} empty tenant_embd_id knowledgebase.")
        kb_groups: dict = {}
        for obj in empty_tenant_embd_id_kbs:
            if kb_groups.get((obj.tenant_id, obj.embd_id)):
                kb_groups[(obj.tenant_id, obj.embd_id)].append(obj.id)
            else:
                kb_groups[(obj.tenant_id, obj.embd_id)] = [obj.id]
        update_cnt = 0
        for k, v in kb_groups.items():
            tenant_llm = TenantLLMService.get_api_key(k[0], k[1])
            if tenant_llm:
                update_cnt += KnowledgebaseService.filter_update([Knowledgebase.id.in_(v)], {"tenant_embd_id": tenant_llm.id})
        logging.info(f"Update {update_cnt} tenant_embd_id in table knowledgebase.")
    # dialog
    empty_tenant_llm_id_dialog = DialogService.get_null_tenant_llm_id_row()
    if empty_tenant_llm_id_dialog:
        logging.info(f"Found {len(empty_tenant_llm_id_dialog)} empty tenant_llm_id dialogs.")
        dialog_groups: dict = {}
        for obj in empty_tenant_llm_id_dialog:
            if dialog_groups.get((obj.tenant_id, obj.llm_id)):
                dialog_groups[(obj.tenant_id, obj.llm_id)].append(obj.id)
            else:
                dialog_groups[(obj.tenant_id, obj.llm_id)] = [obj.id]
        update_cnt = 0
        for k, v in dialog_groups.items():
            tenant_llm = TenantLLMService.get_api_key(k[0], k[1])
            if tenant_llm:
                update_cnt += DialogService.filter_update([Dialog.id.in_(v)], {"tenant_llm_id": tenant_llm.id})
        logging.info(f"Update {update_cnt} tenant_llm_id in table dialog.")

    empty_tenant_rerank_id_dialog = DialogService.get_null_tenant_rerank_id_row()
    if empty_tenant_rerank_id_dialog:
        logging.info(f"Found {len(empty_tenant_rerank_id_dialog)} empty tenant_rerank_id dialogs.")
        dialog_groups: dict = {}
        for obj in empty_tenant_rerank_id_dialog:
            if dialog_groups.get((obj.tenant_id, obj.rerank_id)):
                dialog_groups[(obj.tenant_id, obj.rerank_id)].append(obj.id)
            else:
                dialog_groups[(obj.tenant_id, obj.rerank_id)] = [obj.id]
        update_cnt = 0
        for k, v in dialog_groups.items():
            tenant_llm = TenantLLMService.get_api_key(k[0], k[1])
            if tenant_llm:
                update_cnt += DialogService.filter_update([Dialog.id.in_(v)], {"tenant_rerank_id": tenant_llm.id})
        logging.info(f"Update {update_cnt} tenant_rerank_id in table dialog.")
    # memory
    empty_tenant_embd_id_memories = MemoryService.get_null_tenant_embd_id_row()
    if empty_tenant_embd_id_memories:
        logging.info(f"Found {len(empty_tenant_embd_id_memories)} empty tenant_embd_id memories.")
        memory_groups: dict = {}
        for obj in empty_tenant_embd_id_memories:
            if memory_groups.get((obj.tenant_id, obj.embd_id)):
                memory_groups[(obj.tenant_id, obj.embd_id)].append(obj.id)
            else:
                memory_groups[(obj.tenant_id, obj.embd_id)] = [obj.id]
        update_cnt = 0
        for k, v in memory_groups.items():
            tenant_llm = TenantLLMService.get_api_key(k[0], k[1])
            if tenant_llm:
                update_cnt += MemoryService.filter_update([Memory.id.in_(v)], {"tenant_embd_id": tenant_llm.id})
        logging.info(f"Update {update_cnt} tenant_embd_id in table memory.")

    empty_tenant_llm_id_memories = MemoryService.get_null_tenant_llm_id_row()
    if empty_tenant_llm_id_memories:
        logging.info(f"Found {len(empty_tenant_llm_id_memories)} empty tenant_llm_id memories.")
        memory_groups: dict = {}
        for obj in empty_tenant_llm_id_memories:
            if memory_groups.get((obj.tenant_id, obj.llm_id)):
                memory_groups[(obj.tenant_id, obj.llm_id)].append(obj.id)
            else:
                memory_groups[(obj.tenant_id, obj.llm_id)] = [obj.id]
        update_cnt = 0
        for k, v in memory_groups.items():
            tenant_llm = TenantLLMService.get_api_key(k[0], k[1])
            if tenant_llm:
                update_cnt += MemoryService.filter_update([Memory.id.in_(v)], {"tenant_llm_id": tenant_llm.id})
        logging.info(f"Update {update_cnt} tenant_llm_id in table memory.")
    # tenant
    empty_tenant_model_id_tenants = TenantService.get_null_tenant_model_id_rows()
    if empty_tenant_model_id_tenants:
        logging.info(f"Found {len(empty_tenant_model_id_tenants)} empty tenant_model_id tenants.")
        update_cnt = 0
        for obj in empty_tenant_model_id_tenants:
            tenant_dict = obj.to_dict()
            update_dict = {}
            for key in ["llm_id", "embd_id", "asr_id", "img2txt_id", "rerank_id", "tts_id"]:
                if tenant_dict.get(key) and not tenant_dict.get(f"tenant_{key}"):
                    tenant_model = TenantLLMService.get_api_key(tenant_dict["id"], tenant_dict[key])
                    if tenant_model:
                        update_dict.update({f"tenant_{key}": tenant_model.id})
            if update_dict:
                update_cnt += TenantService.update_by_id(tenant_dict["id"], update_dict)
        logging.info(f"Update {update_cnt} tenant_model_id in table tenant.")
    logging.info("Fix empty tenant_model_id done.")