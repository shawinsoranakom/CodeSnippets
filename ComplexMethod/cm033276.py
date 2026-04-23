def _sync_progress(cls, docs: list[dict]):
        from api.db.services.task_service import TaskService

        for d in docs:
            try:
                tsks = TaskService.query(doc_id=d["id"], order_by=Task.create_time)
                if not tsks:
                    continue
                msg = []
                prg = 0
                finished = True
                bad = 0
                e, doc = DocumentService.get_by_id(d["id"])
                status = doc.run  # TaskStatus.RUNNING.value
                if status == TaskStatus.CANCEL.value:
                    continue
                doc_progress = doc.progress if doc and doc.progress else 0.0
                special_task_running = False
                priority = 0
                for t in tsks:
                    task_type = (t.task_type or "").lower()
                    if task_type in PIPELINE_SPECIAL_PROGRESS_FREEZE_TASK_TYPES:
                        special_task_running = True
                    if 0 <= t.progress < 1:
                        finished = False
                    if t.progress == -1:
                        bad += 1
                    prg += t.progress if t.progress >= 0 else 0
                    if t.progress_msg.strip():
                        msg.append(t.progress_msg)
                    priority = max(priority, t.priority)
                prg /= len(tsks)
                if finished and bad:
                    prg = -1
                    status = TaskStatus.FAIL.value
                elif finished:
                    prg = 1
                    status = TaskStatus.DONE.value
                elif not finished:
                    status = TaskStatus.RUNNING.value

                # only for special task and parsed docs and unfinished
                freeze_progress = special_task_running and doc_progress >= 1 and not finished
                msg = "\n".join(sorted(msg))
                begin_at = d.get("process_begin_at")
                if not begin_at:
                    begin_at = datetime.now()
                    # fallback
                    cls.update_by_id(d["id"], {"process_begin_at": begin_at})

                info = {"process_duration": max(datetime.timestamp(datetime.now()) - begin_at.timestamp(), 0), "run": status}
                if prg != 0 and not freeze_progress:
                    info["progress"] = prg
                if msg:
                    info["progress_msg"] = msg
                    if msg.endswith("created task graphrag") or msg.endswith("created task raptor") or msg.endswith("created task mindmap"):
                        info["progress_msg"] += "\n%d tasks are ahead in the queue..." % get_queue_length(priority)
                else:
                    info["progress_msg"] = "%d tasks are ahead in the queue..." % get_queue_length(priority)
                info["update_time"] = current_timestamp()
                info["update_date"] = get_format_time()
                (cls.model.update(info).where((cls.model.id == d["id"]) & ((cls.model.run.is_null(True)) | (cls.model.run != TaskStatus.CANCEL.value))).execute())
            except Exception as e:
                if str(e).find("'0'") < 0:
                    logging.exception("fetch task exception")