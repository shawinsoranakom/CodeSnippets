async def handle_task():
    global DONE_TASKS, FAILED_TASKS
    redis_msg, task = await collect()
    if not task:
        await asyncio.sleep(5)
        return

    task_type = task["task_type"]
    pipeline_task_type = TASK_TYPE_TO_PIPELINE_TASK_TYPE.get(task_type,
                                                             PipelineTaskType.PARSE) or PipelineTaskType.PARSE
    task_id = task["id"]
    try:
        logging.info(f"handle_task begin for task {json.dumps(task)}")
        CURRENT_TASKS[task["id"]] = copy.deepcopy(task)
        await do_handle_task(task)
        DONE_TASKS += 1
        CURRENT_TASKS.pop(task_id, None)
        logging.info(f"handle_task done for task {json.dumps(task)}")
    except TaskCanceledException as e:
        DONE_TASKS += 1
        CURRENT_TASKS.pop(task_id, None)
        logging.info(
            f"handle_task canceled for task {task_id}: {getattr(e, 'msg', str(e))}"
        )
    except Exception as e:
        FAILED_TASKS += 1
        CURRENT_TASKS.pop(task_id, None)
        try:
            err_msg = str(e)
            while isinstance(e, exceptiongroup.ExceptionGroup):
                e = e.exceptions[0]
                err_msg += ' -- ' + str(e)
            set_progress(task_id, prog=-1, msg=f"[Exception]: {err_msg}")
        except Exception as e:
            logging.exception(f"[Exception]: {str(e)}")
            pass
        logging.exception(f"handle_task got exception for task {json.dumps(task)}")
    finally:
        if not task.get("dataflow_id", ""):
            referred_document_id = None
            if task_type in ["graphrag", "raptor", "mindmap"]:
                referred_document_id = task["doc_ids"][0]
            PipelineOperationLogService.record_pipeline_operation(document_id=task["doc_id"], pipeline_id="",
                                                                  task_type=pipeline_task_type,
                                                                  task_id=task_id, referred_document_id=referred_document_id)

    redis_msg.ack()