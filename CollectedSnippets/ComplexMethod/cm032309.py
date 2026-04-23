def insert(self, documents: list[dict], index_name: str, memory_id: str = None) -> list[str]:
        """Insert messages into memory storage."""
        if not documents:
            return []

        vector_size = len(documents[0].get("content_embed", [])) if "content_embed" in documents[0] else 0

        if not self._check_table_exists_cached(index_name):
            if vector_size == 0:
                raise ValueError("Cannot infer vector size from documents")
            self.create_idx(index_name, memory_id, vector_size)
        elif vector_size > 0:
            # Table exists but may not have the required vector column
            self._ensure_vector_column_exists(index_name, vector_size)

        docs: list[dict] = []
        ids: list[str] = []

        for document in documents:
            d = self.map_message_to_ob_fields(document)
            ids.append(d["id"])

            for column_name in COLUMN_NAMES:
                if column_name not in d:
                    d[column_name] = None

            docs.append(d)

        self.logger.debug("OBConnection.insert messages: %s", ids)

        res = []
        try:
            self.client.upsert(index_name, docs)
        except Exception as e:
            self.logger.error(f"OBConnection.insert error: {str(e)}")
            res.append(str(e))
        return res