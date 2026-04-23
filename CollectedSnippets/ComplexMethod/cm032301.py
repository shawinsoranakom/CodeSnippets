def list_message(cls, uid: str, memory_id: str, agent_ids: List[str]=None, keywords: str=None, page: int=1, page_size: int=50):
        index = index_name(uid)
        filter_dict = {}
        if agent_ids:
            filter_dict["agent_id"] = agent_ids
        if keywords:
            filter_dict["session_id"] = keywords
        select_fields = [
            "message_id", "message_type", "source_id", "memory_id", "user_id", "agent_id", "session_id", "valid_at",
            "invalid_at", "forget_at", "status"
        ]
        order_by = OrderByExpr()
        order_by.desc("valid_at")
        res, total_count = settings.msgStoreConn.search(
            select_fields=select_fields,
            highlight_fields=[],
            condition={**filter_dict, "message_type": MemoryType.RAW.name.lower()},
            match_expressions=[], order_by=order_by,
            offset=(page-1)*page_size, limit=page_size,
            index_names=index, memory_ids=[memory_id], agg_fields=[], hide_forgotten=False
        )
        if not total_count:
            return {
            "message_list": [],
            "total_count": 0
        }

        raw_msg_mapping = settings.msgStoreConn.get_fields(res, select_fields)
        raw_messages = list(raw_msg_mapping.values())
        extract_filter = {"source_id": [r["message_id"] for r in raw_messages]}
        extract_res, _ = settings.msgStoreConn.search(
            select_fields=select_fields,
            highlight_fields=[],
            condition=extract_filter,
            match_expressions=[], order_by=order_by,
            offset=0, limit=512,
            index_names=index, memory_ids=[memory_id], agg_fields=[], hide_forgotten=False
        )
        extract_msg = settings.msgStoreConn.get_fields(extract_res, select_fields)
        grouped_extract_msg = {}
        for msg in extract_msg.values():
            if grouped_extract_msg.get(msg["source_id"]):
                grouped_extract_msg[msg["source_id"]].append(msg)
            else:
                grouped_extract_msg[msg["source_id"]] = [msg]

        for raw_msg in raw_messages:
            raw_msg["extract"] = grouped_extract_msg.get(raw_msg["message_id"], [])

        return {
            "message_list": raw_messages,
            "total_count": total_count
        }