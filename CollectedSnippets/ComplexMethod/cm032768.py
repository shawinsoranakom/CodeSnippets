async def collect():
    global CONSUMER_NAME, DONE_TASKS, FAILED_TASKS
    global UNACKED_ITERATOR

    svr_queue_names = settings.get_svr_queue_names()
    redis_msg = None
    try:
        if not UNACKED_ITERATOR:
            UNACKED_ITERATOR = REDIS_CONN.get_unacked_iterator(svr_queue_names, SVR_CONSUMER_GROUP_NAME, CONSUMER_NAME)
        try:
            redis_msg = next(UNACKED_ITERATOR)
        except StopIteration:
            for svr_queue_name in svr_queue_names:
                redis_msg = REDIS_CONN.queue_consumer(svr_queue_name, SVR_CONSUMER_GROUP_NAME, CONSUMER_NAME)
                if redis_msg:
                    break
    except Exception as e:
        logging.exception(f"collect got exception: {e}")
        return None, None

    if not redis_msg:
        return None, None
    msg = redis_msg.get_message()
    if not msg:
        logging.error(f"collect got empty message of {redis_msg.get_msg_id()}")
        redis_msg.ack()
        return None, None

    canceled = False
    if msg.get("doc_id", "") in [GRAPH_RAPTOR_FAKE_DOC_ID, CANVAS_DEBUG_DOC_ID]:
        task = msg
        if task["task_type"] in PIPELINE_SPECIAL_PROGRESS_FREEZE_TASK_TYPES:
            task = TaskService.get_task(msg["id"], msg["doc_ids"])
            if task:
                task["doc_id"] = msg["doc_id"]
                task["doc_ids"] = msg.get("doc_ids", []) or []
    elif msg.get("task_type") == PipelineTaskType.MEMORY.lower():
        _, task_obj = TaskService.get_by_id(msg["id"])
        task = task_obj.to_dict()
    else:
        task = TaskService.get_task(msg["id"])

    if task:
        canceled = has_canceled(task["id"])
    if not task or canceled:
        state = "is unknown" if not task else "has been cancelled"
        FAILED_TASKS += 1
        logging.warning(f"collect task {msg['id']} {state}")
        redis_msg.ack()
        return None, None

    task_type = msg.get("task_type", "")
    task["task_type"] = task_type
    if task_type[:8] == "dataflow":
        task["tenant_id"] = msg["tenant_id"]
        task["dataflow_id"] = msg["dataflow_id"]
        task["kb_id"] = msg.get("kb_id", "")
    if task_type[:6] == "memory":
        task["memory_id"] = msg["memory_id"]
        task["source_id"] = msg["source_id"]
        task["message_dict"] = msg["message_dict"]
    return redis_msg, task