def get_fields(self, res, fields: list[str]) -> dict[str, dict]:
        """Get fields from search result."""
        if isinstance(res, tuple):
            res = res[0]

        res_fields = {}
        if not fields:
            return {}

        messages = res.messages if hasattr(res, 'messages') else []

        for doc in messages:
            message = self.get_message_from_ob_doc(doc)
            m = {}
            for n, v in message.items():
                if n not in fields:
                    continue
                if isinstance(v, list):
                    m[n] = v
                    continue
                if n in ["message_id", "source_id", "valid_at", "invalid_at", "forget_at", "status"] and isinstance(v,
                                                                                                                    (int,
                                                                                                                     float,
                                                                                                                     bool)):
                    m[n] = v
                    continue
                if not isinstance(v, str):
                    m[n] = str(v) if v is not None else ""
                else:
                    m[n] = v

            doc_id = doc.get("id") or message.get("id")
            if m and doc_id:
                res_fields[doc_id] = m

        return res_fields