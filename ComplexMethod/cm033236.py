def create(cls, document_id, pipeline_id, task_type, task_id=None, referred_document_id=None, dsl: str = "{}"):
        if document_id != GRAPH_RAPTOR_FAKE_DOC_ID:
            referred_document_id = document_id

        # no need to update document for graph rag, raptor mindmap task
        if task_type not in [PipelineTaskType.GRAPH_RAG, PipelineTaskType.RAPTOR, PipelineTaskType.MINDMAP]:
            ok, document = DocumentService.get_by_id(referred_document_id)
            if not ok:
                logging.warning(f"Document for referred_document_id {referred_document_id} not found")
                return None
            DocumentService.update_progress_immediately([document.to_dict()])

        ok, document = DocumentService.get_by_id(referred_document_id)
        if not ok:
            logging.warning(f"Document for referred_document_id {referred_document_id} not found")
            return None

        # From document
        title = document.parser_id
        avatar = document.thumbnail
        document_name = document.name
        operation_status = document.run
        progress = document.progress
        progress_msg = document.progress_msg
        process_begin_at = document.process_begin_at
        process_duration = document.process_duration

        if pipeline_id:
            ok, user_pipeline = UserCanvasService.get_by_id(pipeline_id)
            if not ok:
                raise RuntimeError(f"Pipeline {pipeline_id} not found")
            tenant_id = user_pipeline.user_id
            title = user_pipeline.title
            avatar = user_pipeline.avatar
        else:
            ok, kb_info = KnowledgebaseService.get_by_id(document.kb_id)
            if not ok:
                raise RuntimeError(f"Cannot find dataset {document.kb_id} for referred_document {referred_document_id}")
            tenant_id = kb_info.tenant_id

        if task_type not in VALID_PIPELINE_TASK_TYPES:
            raise ValueError(f"Invalid task type: {task_type}")

        if task_type in [PipelineTaskType.GRAPH_RAG, PipelineTaskType.RAPTOR, PipelineTaskType.MINDMAP]:
            # query task to get progress information from task
            ok, task = TaskService.get_by_id(task_id)
            if not ok:
                raise RuntimeError(f"Task not found for dataset {document.kb_id}")
            title = task_type
            document_name = task_type
            operation_status = TaskStatus.DONE if task.progress == 1 else TaskStatus.FAIL
            progress = task.progress
            progress_msg = task.progress_msg
            process_begin_at = task.begin_at
            process_duration = task.process_duration

            finish_at = process_begin_at + timedelta(seconds=process_duration)
            if task_type == PipelineTaskType.GRAPH_RAG:
                KnowledgebaseService.update_by_id(
                    document.kb_id,
                    {"graphrag_task_finish_at": finish_at},
                )
            elif task_type == PipelineTaskType.RAPTOR:
                KnowledgebaseService.update_by_id(
                    document.kb_id,
                    {"raptor_task_finish_at": finish_at},
                )
            elif task_type == PipelineTaskType.MINDMAP:
                KnowledgebaseService.update_by_id(
                    document.kb_id,
                    {"mindmap_task_finish_at": finish_at},
                )

        log = dict(
            id=get_uuid(),
            document_id=document_id,  # GRAPH_RAPTOR_FAKE_DOC_ID or real document_id
            tenant_id=tenant_id,
            kb_id=document.kb_id,
            pipeline_id=pipeline_id,
            pipeline_title=title,
            parser_id=document.parser_id,
            document_name=document_name,
            document_suffix=document.suffix,
            document_type=document.type,
            source_from=document.source_type.split("/")[0],
            progress=progress,
            progress_msg=progress_msg,
            process_begin_at=process_begin_at,
            process_duration=process_duration,
            dsl=json.loads(dsl),
            task_type=task_type,
            operation_status=operation_status,
            avatar=avatar,
        )
        timestamp = current_timestamp()
        datetime_now = datetime_format(datetime.now())
        log["create_time"] = timestamp
        log["create_date"] = datetime_now
        log["update_time"] = timestamp
        log["update_date"] = datetime_now
        with DB.atomic():
            obj = cls.save(**log)

            limit = int(os.getenv("PIPELINE_OPERATION_LOG_LIMIT", 1000))
            total = cls.model.select().where(cls.model.kb_id == document.kb_id).count()

            if total > limit:
                keep_ids = [m.id for m in cls.model.select(cls.model.id).where(cls.model.kb_id == document.kb_id).order_by(cls.model.create_time.desc()).limit(limit)]

                deleted = cls.model.delete().where(cls.model.kb_id == document.kb_id, cls.model.id.not_in(keep_ids)).execute()
                logging.info(f"[PipelineOperationLogService] Cleaned {deleted} old logs, kept latest {limit} for {document.kb_id}")

        return obj