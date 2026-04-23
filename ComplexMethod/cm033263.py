def queue_tasks(doc: dict, bucket: str, name: str, priority: int):
    """Create and queue document processing tasks.

    This function creates processing tasks for a document based on its type and configuration.
    It handles different document types (PDF, Excel, etc.) differently and manages task
    chunking and configuration. It also implements task reuse optimization by checking
    for previously completed tasks.

    Args:
        doc (dict): Document dictionary containing metadata and configuration.
        bucket (str): Storage bucket name where the document is stored.
        name (str): File name of the document.
        priority (int, optional): Priority level for task queueing (default is 0).

    Note:
        - For PDF documents, tasks are created per page range based on configuration
        - For Excel documents, tasks are created per row range
        - Task digests are calculated for optimization and reuse
        - Previous task chunks may be reused if available
    """

    def new_task():
        return {
            "id": get_uuid(),
            "doc_id": doc["id"],
            "progress": 0.0,
            "from_page": 0,
            "to_page": 100000000,
            "begin_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    parse_task_array = []

    if doc["type"] == FileType.PDF.value:
        file_bin = settings.STORAGE_IMPL.get(bucket, name)
        do_layout = doc["parser_config"].get("layout_recognize", "DeepDOC")
        pages = PdfParser.total_page_number(doc["name"], file_bin)
        if pages is None:
            pages = 0
        page_size = doc["parser_config"].get("task_page_size") or 12
        if doc["parser_id"] == "paper":
            page_size = doc["parser_config"].get("task_page_size") or 22
        if doc["parser_id"] in ["one", "knowledge_graph"] or do_layout != "DeepDOC" or doc["parser_config"].get("toc_extraction", False):
            page_size = 10 ** 9
        page_ranges = doc["parser_config"].get("pages") or [(1, 10 ** 5)]
        for s, e in page_ranges:
            s -= 1
            s = max(0, s)
            e = min(e - 1, pages)
            for p in range(s, e, page_size):
                task = new_task()
                task["from_page"] = p
                task["to_page"] = min(p + page_size, e)
                parse_task_array.append(task)

    elif doc["parser_id"] == "table":
        file_bin = settings.STORAGE_IMPL.get(bucket, name)
        rn = RAGFlowExcelParser.row_number(doc["name"], file_bin)
        for i in range(0, rn, 3000):
            task = new_task()
            task["from_page"] = i
            task["to_page"] = min(i + 3000, rn)
            parse_task_array.append(task)
    else:
        parse_task_array.append(new_task())

    chunking_config = DocumentService.get_chunking_config(doc["id"])
    for task in parse_task_array:
        hasher = xxhash.xxh64()
        for field in sorted(chunking_config.keys()):
            if field == "parser_config":
                for k in ["raptor", "graphrag"]:
                    if k in chunking_config[field]:
                        del chunking_config[field][k]
            hasher.update(str(chunking_config[field]).encode("utf-8"))
        for field in ["doc_id", "from_page", "to_page"]:
            hasher.update(str(task.get(field, "")).encode("utf-8"))
        task_digest = hasher.hexdigest()
        task["digest"] = task_digest
        task["progress"] = 0.0
        task["priority"] = priority

    prev_tasks = TaskService.get_tasks(doc["id"])
    ck_num = 0
    if prev_tasks:
        for task in parse_task_array:
            ck_num += reuse_prev_task_chunks(task, prev_tasks, chunking_config)
        TaskService.filter_delete([Task.doc_id == doc["id"]])
        pre_chunk_ids = []
        for pre_task in prev_tasks:
            if pre_task["chunk_ids"]:
                pre_chunk_ids.extend(pre_task["chunk_ids"].split())
        if pre_chunk_ids:
            settings.docStoreConn.delete({"id": pre_chunk_ids}, search.index_name(chunking_config["tenant_id"]),
                                         chunking_config["kb_id"])
    DocumentService.update_by_id(doc["id"], {"chunk_num": ck_num})

    bulk_insert_into_db(Task, parse_task_array, True)
    DocumentService.begin2parse(doc["id"])

    unfinished_task_array = [task for task in parse_task_array if task["progress"] < 1.0]
    for unfinished_task in unfinished_task_array:
        assert REDIS_CONN.queue_product(
            settings.get_svr_queue_name(priority), message=unfinished_task
        ), "Can't access Redis. Please check the Redis' status."