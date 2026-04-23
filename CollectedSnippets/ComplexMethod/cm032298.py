def _get_documents_status(self, document_ids):
        import time
        terminal_states = {"DONE", "FAIL", "CANCEL"}
        interval_sec = 1
        pending = set(document_ids)
        finished = []
        while pending:
            for doc_id in list(pending):
                def fetch_doc(doc_id: str) -> Document | None:
                    try:
                        docs = self.list_documents(id=doc_id)
                        return docs[0] if docs else None
                    except Exception:
                        return None
                doc = fetch_doc(doc_id)
                if doc is None:
                    continue
                if isinstance(doc.run, str) and doc.run.upper() in terminal_states:
                    finished.append((doc_id, doc.run, doc.chunk_count, doc.token_count))
                    pending.discard(doc_id)
                elif float(doc.progress or 0.0) >= 1.0:
                    finished.append((doc_id, "DONE", doc.chunk_count, doc.token_count))
                    pending.discard(doc_id)
            if pending:
                time.sleep(interval_sec)
        return finished