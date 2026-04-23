async def insert_chunks(task_id, task_tenant_id, task_dataset_id, chunks, progress_callback):
    """
    Insert chunks into document store (Elasticsearch OR Infinity).

    Args:
        task_id: Task identifier
        task_tenant_id: Tenant ID
        task_dataset_id: Dataset/knowledge base ID
        chunks: List of chunk dictionaries to insert
        progress_callback: Callback function for progress updates
    """
    mothers = []
    mother_ids = set([])
    for ck in chunks:
        mom = ck.get("mom") or ck.get("mom_with_weight") or ""
        if not mom:
            continue
        id = xxhash.xxh64(mom.encode("utf-8")).hexdigest()
        ck["mom_id"] = id
        if id in mother_ids:
            continue
        mother_ids.add(id)
        mom_ck = copy.deepcopy(ck)
        mom_ck["id"] = id
        mom_ck["content_with_weight"] = mom
        mom_ck["available_int"] = 0
        flds = list(mom_ck.keys())
        for fld in flds:
            if fld not in ["id", "content_with_weight", "doc_id", "docnm_kwd", "kb_id", "available_int",
                           "position_int", "create_timestamp_flt", "page_num_int", "top_int"]:
                del mom_ck[fld]
        mothers.append(mom_ck)

    for b in range(0, len(mothers), settings.DOC_BULK_SIZE):
        await thread_pool_exec(settings.docStoreConn.insert, mothers[b:b + settings.DOC_BULK_SIZE],
                                search.index_name(task_tenant_id), task_dataset_id, )
        task_canceled = has_canceled(task_id)
        if task_canceled:
            progress_callback(-1, msg="Task has been canceled.")
            return False

    for b in range(0, len(chunks), settings.DOC_BULK_SIZE):
        doc_store_result = await thread_pool_exec(settings.docStoreConn.insert, chunks[b:b + settings.DOC_BULK_SIZE],
                                                   search.index_name(task_tenant_id), task_dataset_id, )
        task_canceled = has_canceled(task_id)
        if task_canceled:
            progress_callback(-1, msg="Task has been canceled.")
            return False
        if b % 128 == 0:
            progress_callback(prog=0.8 + 0.1 * (b + 1) / len(chunks), msg="")
        if doc_store_result:
            error_message = f"Insert chunk error: {doc_store_result}, please check log file and Elasticsearch/Infinity status!"
            progress_callback(-1, msg=error_message)
            raise Exception(error_message)
        chunk_ids = [chunk["id"] for chunk in chunks[:b + settings.DOC_BULK_SIZE]]
        chunk_ids_str = " ".join(chunk_ids)
        try:
            TaskService.update_chunk_ids(task_id, chunk_ids_str)
        except DoesNotExist:
            logging.warning(f"do_handle_task update_chunk_ids failed since task {task_id} is unknown.")
            doc_store_result = await thread_pool_exec(settings.docStoreConn.delete, {"id": chunk_ids},
                                                       search.index_name(task_tenant_id), task_dataset_id, )
            tasks = []
            for chunk_id in chunk_ids:
                tasks.append(asyncio.create_task(delete_image(task_dataset_id, chunk_id)))
            try:
                await asyncio.gather(*tasks, return_exceptions=False)
            except Exception as e:
                logging.error(f"delete_image failed: {e}")
                for t in tasks:
                    t.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
                raise
            progress_callback(-1, msg=f"Chunk updates failed since task {task_id} is unknown.")
            return False
    return True