async def retrieval_by_toc(self, query: str, chunks: list[dict], tenant_ids: list[str], chat_mdl, topn: int = 6):
        from rag.prompts.generator import relevant_chunks_with_toc # moved from the top of the file to avoid circular import
        if not chunks:
            return []
        idx_nms = [index_name(tid) for tid in tenant_ids]
        ranks, doc_id2kb_id = {}, {}
        for ck in chunks:
            if ck["doc_id"] not in ranks:
                ranks[ck["doc_id"]] = 0
            ranks[ck["doc_id"]] += ck["similarity"]
            doc_id2kb_id[ck["doc_id"]] = ck["kb_id"]
        doc_id = sorted(ranks.items(), key=lambda x: x[1] * -1.)[0][0]
        kb_ids = [doc_id2kb_id[doc_id]]
        es_res = self.dataStore.search(["content_with_weight"], [], {"doc_id": doc_id, "toc_kwd": "toc"}, [],
                                       OrderByExpr(), 0, 128, idx_nms,
                                       kb_ids)
        toc = []
        dict_chunks = self.dataStore.get_fields(es_res, ["content_with_weight"])
        for _, doc in dict_chunks.items():
            try:
                toc.extend(json.loads(doc["content_with_weight"]))
            except Exception as e:
                logging.exception(e)
        if not toc:
            return chunks

        ids = await relevant_chunks_with_toc(query, toc, chat_mdl, topn * 2)
        if not ids:
            return chunks

        vector_size = 1024
        id2idx = {ck["chunk_id"]: i for i, ck in enumerate(chunks)}
        for cid, sim in ids:
            if cid in id2idx:
                chunks[id2idx[cid]]["similarity"] += sim
                continue
            chunk = self.dataStore.get(cid, idx_nms[0], kb_ids)
            if not chunk:
                continue
            d = {
                "chunk_id": cid,
                "content_ltks": chunk["content_ltks"],
                "content_with_weight": chunk["content_with_weight"],
                "doc_id": doc_id,
                "docnm_kwd": chunk.get("docnm_kwd", ""),
                "kb_id": chunk["kb_id"],
                "important_kwd": chunk.get("important_kwd", []),
                "image_id": chunk.get("img_id", ""),
                "similarity": sim,
                "vector_similarity": sim,
                "term_similarity": sim,
                "vector": [0.0] * vector_size,
                "positions": chunk.get("position_int", []),
                "doc_type_kwd": chunk.get("doc_type_kwd", "")
            }
            for k in chunk.keys():
                if k[-4:] == "_vec":
                    d["vector"] = chunk[k]
                    vector_size = len(chunk[k])
                    break
            chunks.append(d)

        return sorted(chunks, key=lambda x: x["similarity"] * -1)[:topn]