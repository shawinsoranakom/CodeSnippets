def get_fields(self, res, fields: list[str]) -> dict[str, dict]:
        res_fields = {}
        if not fields:
            return {}
        for doc in self._get_source(res):
            message = self.get_message_from_es_doc(doc)
            m = {}
            for n, v in message.items():
                if n not in fields:
                    continue
                if isinstance(v, list):
                    m[n] = v
                    continue
                if n in ["message_id", "source_id", "valid_at", "invalid_at", "forget_at", "status"] and isinstance(v, (int, float, bool)):
                    m[n] = v
                    continue
                if not isinstance(v, str):
                    m[n] = str(v)
                else:
                    m[n] = v

            if m:
                res_fields[doc["id"]] = m
        return res_fields