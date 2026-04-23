async def _async_update_chunk_info(self, chunk_info, kbinfos):
        async with self._lock:
            """Update chunk information for citations"""
            if not chunk_info["chunks"]:
                # If this is the first retrieval, use the retrieval results directly
                for k in chunk_info.keys():
                    chunk_info[k] = kbinfos[k]
            else:
                # Merge newly retrieved information, avoiding duplicates
                cids = [c["chunk_id"] for c in chunk_info["chunks"]]
                for c in kbinfos["chunks"]:
                    if c["chunk_id"] not in cids:
                        chunk_info["chunks"].append(c)

                dids = [d["doc_id"] for d in chunk_info["doc_aggs"]]
                for d in kbinfos["doc_aggs"]:
                    if d["doc_id"] not in dids:
                        chunk_info["doc_aggs"].append(d)