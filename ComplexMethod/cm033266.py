def schedule(cls, connector_id, kb_id, poll_range_start=None, reindex=False, total_docs_indexed=0):
        try:
            if cls.model.select().where(cls.model.kb_id == kb_id, cls.model.connector_id == connector_id).count() > 100:
                rm_ids = [m.id for m in cls.model.select(cls.model.id).where(cls.model.kb_id == kb_id, cls.model.connector_id == connector_id).order_by(cls.model.update_time.asc()).limit(70)]
                deleted = cls.model.delete().where(cls.model.id.in_(rm_ids)).execute()
                logging.info(f"[SyncLogService] Cleaned {deleted} old logs.")
        except Exception as e:
            logging.exception(e)

        try:
            e = cls.query(kb_id=kb_id, connector_id=connector_id, status=TaskStatus.SCHEDULE)
            if e:
                logging.warning(f"{kb_id}--{connector_id} has already had a scheduling sync task which is abnormal.")
                return None
            reindex = "1" if reindex else "0"
            ConnectorService.update_by_id(connector_id, {"status": TaskStatus.SCHEDULE})
            return cls.save(**{
                "id": get_uuid(),
                "kb_id": kb_id, "status": TaskStatus.SCHEDULE, "connector_id": connector_id,
                "poll_range_start": poll_range_start, "from_beginning": reindex,
                "total_docs_indexed": total_docs_indexed
            })
        except Exception as e:
            logging.exception(e)
            task = cls.get_latest_task(connector_id, kb_id)
            if task:
                cls.model.update(status=TaskStatus.SCHEDULE,
                                 poll_range_start=poll_range_start,
                                 error_msg=cls.model.error_msg + str(e),
                                 full_exception_trace=cls.model.full_exception_trace + str(e)
                                 ) \
                .where(cls.model.id == task.id).execute()
                ConnectorService.update_by_id(connector_id, {"status": TaskStatus.SCHEDULE})