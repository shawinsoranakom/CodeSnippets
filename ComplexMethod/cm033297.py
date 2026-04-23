def delete_user_data(user_id: str) -> dict:
    # use user_id to delete
    usr = UserService.filter_by_id(user_id)
    if not usr:
        return {"success": False, "message": f"{user_id} can't be found."}
    # check is inactive and not admin
    if usr.is_active == ActiveEnum.ACTIVE.value:
        return {"success": False, "message": f"{user_id} is active and can't be deleted."}
    if usr.is_superuser:
        return {"success": False, "message": "Can't delete the super user."}
    # tenant info
    tenants = UserTenantService.get_user_tenant_relation_by_user_id(usr.id)
    owned_tenant = [t for t in tenants if t["role"] == UserTenantRole.OWNER.value]

    done_msg = ''
    try:
        # step1. delete owned tenant info
        if owned_tenant:
            done_msg += "Start to delete owned tenant.\n"
            tenant_id = owned_tenant[0]["tenant_id"]
            kb_ids = KnowledgebaseService.get_kb_ids(usr.id)
            # step1.1 delete dataset related file and info
            if kb_ids:
                # step1.1.1 delete files in storage, remove bucket
                for kb_id in kb_ids:
                    if settings.STORAGE_IMPL.bucket_exists(kb_id):
                        settings.STORAGE_IMPL.remove_bucket(kb_id)
                done_msg += f"- Removed {len(kb_ids)} dataset's buckets.\n"
                # step1.1.2 delete file and document info in db
                doc_ids = DocumentService.get_all_doc_ids_by_kb_ids(kb_ids)
                if doc_ids:
                    for doc in doc_ids:
                        try:
                            DocMetadataService.delete_document_metadata(doc["id"], doc["kb_id"], tenant_id=None)
                        except Exception as e:
                            logging.warning(f"Failed to delete metadata for document {doc['id']}: {e}")

                    doc_delete_res = DocumentService.delete_by_ids([i["id"] for i in doc_ids])
                    done_msg += f"- Deleted {doc_delete_res} document records.\n"
                    task_delete_res = TaskService.delete_by_doc_ids([i["id"] for i in doc_ids])
                    done_msg += f"- Deleted {task_delete_res} task records.\n"
                file_ids = FileService.get_all_file_ids_by_tenant_id(usr.id)
                if file_ids:
                    file_delete_res = FileService.delete_by_ids([f["id"] for f in file_ids])
                    done_msg += f"- Deleted {file_delete_res} file records.\n"
                if doc_ids or file_ids:
                    file2doc_delete_res = File2DocumentService.delete_by_document_ids_or_file_ids(
                        [i["id"] for i in doc_ids],
                        [f["id"] for f in file_ids]
                    )
                    done_msg += f"- Deleted {file2doc_delete_res} document-file relation records.\n"
                # step1.1.3 delete chunk in es
                r = settings.docStoreConn.delete({"kb_id": kb_ids},
                                         search.index_name(tenant_id), kb_ids)
                done_msg += f"- Deleted {r} chunk records.\n"
                kb_delete_res = KnowledgebaseService.delete_by_ids(kb_ids)
                done_msg += f"- Deleted {kb_delete_res} dataset records.\n"
                # step1.1.4 delete agents
                agent_delete_res = delete_user_agents(usr.id)
                done_msg += f"- Deleted {agent_delete_res['agents_deleted_count']} agent, {agent_delete_res['version_deleted_count']} versions records.\n"
                # step1.1.5 delete dialogs
                dialog_delete_res = delete_user_dialogs(usr.id)
                done_msg += f"- Deleted {dialog_delete_res['dialogs_deleted_count']} dialogs, {dialog_delete_res['conversations_deleted_count']} conversations, {dialog_delete_res['api_token_deleted_count']} api tokens, {dialog_delete_res['api4conversation_deleted_count']} api4conversations.\n"
                # step1.1.6 delete mcp server
                mcp_delete_res = MCPServerService.delete_by_tenant_id(usr.id)
                done_msg += f"- Deleted {mcp_delete_res} MCP server.\n"
                # step1.1.7 delete search
                search_delete_res = SearchService.delete_by_tenant_id(usr.id)
                done_msg += f"- Deleted {search_delete_res} search records.\n"
            # step1.2 delete tenant_llm and tenant_langfuse
            llm_delete_res = TenantLLMService.delete_by_tenant_id(tenant_id)
            done_msg += f"- Deleted {llm_delete_res} tenant-LLM records.\n"
            langfuse_delete_res = TenantLangfuseService.delete_ty_tenant_id(tenant_id)
            done_msg += f"- Deleted {langfuse_delete_res} langfuse records.\n"
            try:
                metadata_index_name = DocMetadataService._get_doc_meta_index_name(tenant_id)
                settings.docStoreConn.delete_idx(metadata_index_name, "")
                done_msg += f"- Deleted metadata table {metadata_index_name}.\n"
            except Exception as e:
                logging.warning(f"Failed to delete metadata table for tenant {tenant_id}: {e}")
                done_msg += "- Warning: Failed to delete metadata table (continuing).\n"
            # step1.3 delete memory and messages
            user_memory = MemoryService.get_by_tenant_id(tenant_id)
            if user_memory:
                for memory in user_memory:
                    if MessageService.has_index(tenant_id, memory.id):
                        MessageService.delete_index(tenant_id, memory.id)
                done_msg += " Deleted memory index."
                memory_delete_res = MemoryService.delete_by_ids([m.id for m in user_memory])
                done_msg += f"Deleted {memory_delete_res} memory datasets."
            # step1.4 delete own tenant
            tenant_delete_res = TenantService.delete_by_id(tenant_id)
            done_msg += f"- Deleted {tenant_delete_res} tenant.\n"
        # step2 delete user-tenant relation
        if tenants:
            # step2.1 delete docs and files in joined team
            joined_tenants = [t for t in tenants if t["role"] == UserTenantRole.NORMAL.value]
            if joined_tenants:
                done_msg += "Start to delete data in joined tenants.\n"
                created_documents = DocumentService.get_all_docs_by_creator_id(usr.id)
                if created_documents:
                    # step2.1.1 delete files
                    doc_file_info = File2DocumentService.get_by_document_ids([d['id'] for d in created_documents])
                    created_files = FileService.get_by_ids([f['file_id'] for f in doc_file_info])
                    if created_files:
                        # step2.1.1.1 delete file in storage
                        for f in created_files:
                            settings.STORAGE_IMPL.rm(f.parent_id, f.location)
                        done_msg += f"- Deleted {len(created_files)} uploaded file.\n"
                        # step2.1.1.2 delete file record
                        file_delete_res = FileService.delete_by_ids([f.id for f in created_files])
                        done_msg += f"- Deleted {file_delete_res} file records.\n"
                    # step2.1.2 delete document-file relation record
                    file2doc_delete_res = File2DocumentService.delete_by_document_ids_or_file_ids(
                        [d['id'] for d in created_documents],
                        [f.id for f in created_files]
                    )
                    done_msg += f"- Deleted {file2doc_delete_res} document-file relation records.\n"
                    # step2.1.3 delete chunks
                    doc_groups = group_by(created_documents, "tenant_id")
                    kb_grouped_doc = {k: group_by(v, "kb_id") for k, v in doc_groups.items()}
                    # chunks in {'tenant_id': {'kb_id': [{'id': doc_id}]}} structure
                    chunk_delete_res = 0
                    kb_doc_info = {}
                    for _tenant_id, kb_doc in kb_grouped_doc.items():
                        for _kb_id, docs in kb_doc.items():
                            chunk_delete_res += settings.docStoreConn.delete(
                                {"doc_id": [d["id"] for d in docs]},
                                search.index_name(_tenant_id), _kb_id
                            )
                            # record doc info
                            if _kb_id in kb_doc_info.keys():
                                kb_doc_info[_kb_id]['doc_num'] += 1
                                kb_doc_info[_kb_id]['token_num'] += sum([d["token_num"] for d in docs])
                                kb_doc_info[_kb_id]['chunk_num'] += sum([d["chunk_num"] for d in docs])
                            else:
                                kb_doc_info[_kb_id] = {
                                    'doc_num': 1,
                                    'token_num': sum([d["token_num"] for d in docs]),
                                    'chunk_num': sum([d["chunk_num"] for d in docs])
                                }
                    done_msg += f"- Deleted {chunk_delete_res} chunks.\n"
                    # step2.1.4 delete tasks
                    task_delete_res = TaskService.delete_by_doc_ids([d['id'] for d in created_documents])
                    done_msg += f"- Deleted {task_delete_res} tasks.\n"
                    # step2.1.5 delete document record
                    doc_delete_res = DocumentService.delete_by_ids([d['id'] for d in created_documents])
                    done_msg += f"- Deleted {doc_delete_res} documents.\n"
                    for doc in created_documents:
                        try:
                            DocMetadataService.delete_document_metadata(doc['id'], doc['kb_id'], doc['tenant_id'])
                        except Exception as e:
                            logging.warning(f"Failed to delete metadata for document {doc['id']}: {e}")
                    # step2.1.6 update dataset doc&chunk&token cnt
                    for kb_id, doc_num in kb_doc_info.items():
                        KnowledgebaseService.decrease_document_num_in_delete(kb_id, doc_num)

            # step2.2 delete relation
            user_tenant_delete_res = UserTenantService.delete_by_ids([t["id"] for t in tenants])
            done_msg += f"- Deleted {user_tenant_delete_res} user-tenant records.\n"
        # step3 finally delete user
        user_delete_res = UserService.delete_by_id(usr.id)
        done_msg += f"- Deleted {user_delete_res} user.\nDelete done!"

        return {"success": True, "message": f"Successfully deleted user. Details:\n{done_msg}"}

    except Exception as e:
        logging.exception(e)
        return {"success": False, "message": "An internal error occurred during user deletion. Some operations may have completed.","details": done_msg}