def apply_feedback(
        cls,
        tenant_id: str,
        reference: dict,
        is_positive: bool
    ) -> dict:
        """
        Apply user feedback to all chunks referenced in a response.

        Args:
            tenant_id: The tenant ID
            reference: The reference dict from the conversation message
            is_positive: True for upvote (thumbup), False for downvote

        Returns:
            Dict with 'success_count', 'fail_count', and 'chunk_ids' processed
        """
        # Check if feature is enabled
        if not CHUNK_FEEDBACK_ENABLED:
            logging.debug("Chunk feedback feature is disabled")
            return {"success_count": 0, "fail_count": 0, "chunk_ids": [], "disabled": True}

        rows = cls._feedback_rows_from_reference(reference)
        chunk_ids = [r[0] for r in rows]

        if not chunk_ids:
            logging.debug("No chunk IDs found in reference for feedback")
            return {"success_count": 0, "fail_count": 0, "chunk_ids": []}

        signed_budget = (
            UPVOTE_WEIGHT_INCREMENT if is_positive else -DOWNVOTE_WEIGHT_DECREMENT
        )
        weighting = CHUNK_FEEDBACK_WEIGHTING if CHUNK_FEEDBACK_WEIGHTING in (
            "uniform",
            "relevance",
        ) else "relevance"

        if weighting == "uniform":
            deltas = _allocate_deltas_uniform([(r[0], r[1]) for r in rows], signed_budget)
        else:
            deltas = _allocate_deltas_relevance(rows, signed_budget)

        success_count = 0
        fail_count = 0

        row_by_chunk = {r[0]: r[2].get("row_id") for r in rows}
        for chunk_id, kb_id, delta in deltas:
            if delta == 0:
                continue
            rid = row_by_chunk.get(chunk_id)
            rid_int = None
            if rid is not None:
                try:
                    rid_int = int(rid)
                except (TypeError, ValueError):
                    pass
            if cls.update_chunk_weight(tenant_id, chunk_id, kb_id, delta, row_id=rid_int):
                success_count += 1
            else:
                fail_count += 1

        logging.info(
            "Applied %s feedback (%s) to %s/%s chunks",
            "positive" if is_positive else "negative",
            weighting,
            success_count,
            len(chunk_ids),
        )

        return {
            "success_count": success_count,
            "fail_count": fail_count,
            "chunk_ids": chunk_ids
        }