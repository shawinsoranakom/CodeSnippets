def update_chunk_weight(
        tenant_id: str,
        chunk_id: str,
        kb_id: str,
        delta: int,
        row_id: int | None = None,
    ) -> bool:
        """
        Update the pagerank weight of a single chunk.

        Elasticsearch, OpenSearch, OceanBase/SeekDB, and Infinity use an
        atomic adjust on the doc store when supported. Infinity passes
        row_id (from retrieval results) for targeted single-row updates.

        Args:
            tenant_id: The tenant ID for index naming
            chunk_id: The chunk ID to update
            kb_id: The knowledgebase ID
            delta: Signed integer weight change (pagerank_fea is stored as int)

        Returns:
            True if update succeeded, False otherwise
        """
        try:
            idx_name = index_name(tenant_id)
            conn = settings.docStoreConn
            adjust = getattr(conn, "adjust_chunk_pagerank_fea", None)
            if callable(adjust):
                kwargs: dict = {}
                if row_id is not None:
                    kwargs["row_id"] = row_id
                success = adjust(
                    chunk_id,
                    idx_name,
                    kb_id,
                    float(delta),
                    MIN_PAGERANK_WEIGHT,
                    MAX_PAGERANK_WEIGHT,
                    **kwargs,
                )
                if success:
                    logging.info(
                        "Adjusted chunk %s pagerank by %s (atomic)",
                        chunk_id,
                        delta,
                    )
                else:
                    logging.warning("Failed atomic pagerank adjust for chunk %s", chunk_id)
                return success

            chunk = conn.get(chunk_id, idx_name, [kb_id])
            if not chunk:
                logging.warning("Chunk %s not found in index %s", chunk_id, idx_name)
                return False

            current_weight = float(chunk.get(PAGERANK_FLD, 0) or 0)
            new_weight = current_weight + float(delta)
            new_weight = max(float(MIN_PAGERANK_WEIGHT), min(float(MAX_PAGERANK_WEIGHT), new_weight))

            condition = {"id": chunk_id}
            doc_engine = settings.DOC_ENGINE.lower()
            if new_weight <= 0.0 and doc_engine in ("elasticsearch", "opensearch"):
                new_value = {"remove": PAGERANK_FLD}
            else:
                new_value = {PAGERANK_FLD: new_weight}

            success = conn.update(condition, new_value, idx_name, kb_id)

            if success:
                logging.info(
                    "Updated chunk %s pagerank: %s -> %s",
                    chunk_id,
                    current_weight,
                    new_weight,
                )
            else:
                logging.warning("Failed to update chunk %s pagerank", chunk_id)

            return success

        except Exception as e:
            logging.exception("Error updating chunk %s weight: %s", chunk_id, e)
            return False