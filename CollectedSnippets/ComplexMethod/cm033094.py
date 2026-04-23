def _extract_remote_document_entries(payload: Any) -> list[dict[str, Any]]:
        if not isinstance(payload, dict):
            return []
        if isinstance(payload.get("document"), dict):
            return [payload["document"]]
        if isinstance(payload.get("documents"), list):
            return [d for d in payload["documents"] if isinstance(d, dict)]
        if isinstance(payload.get("results"), list):
            docs = []
            for it in payload["results"]:
                if isinstance(it, dict):
                    if isinstance(it.get("document"), dict):
                        docs.append(it["document"])
                    elif isinstance(it.get("result"), dict):
                        docs.append(it["result"])
                    else:
                        docs.append(it)
            return docs
        return []