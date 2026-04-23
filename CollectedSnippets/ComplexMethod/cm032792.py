def kb_prompt(kbinfos, max_tokens, hash_id=False):
    from api.db.services.document_service import DocumentService
    from api.db.services.doc_metadata_service import DocMetadataService

    knowledges = [get_value(ck, "content", "content_with_weight") for ck in kbinfos["chunks"]]
    kwlg_len = len(knowledges)
    used_token_count = 0
    chunks_num = 0
    for i, c in enumerate(knowledges):
        if not c:
            continue
        used_token_count += num_tokens_from_string(c)
        chunks_num += 1
        if max_tokens * 0.97 < used_token_count:
            knowledges = knowledges[:i]
            logging.warning(f"Not all the retrieval into prompt: {len(knowledges)}/{kwlg_len}")
            break

    docs = DocumentService.get_by_ids([get_value(ck, "doc_id", "document_id") for ck in kbinfos["chunks"][:chunks_num]])

    docs_with_meta = {}
    for d in docs:
        meta = DocMetadataService.get_document_metadata(d.id)
        docs_with_meta[d.id] = meta if meta else {}
    docs = docs_with_meta

    def draw_node(k, line):
        if line is not None and not isinstance(line, str):
            line = str(line)
        if not line:
            return ""
        return f"\n├── {k}: " + re.sub(r"\n+", " ", line, flags=re.DOTALL)

    knowledges = []
    for i, ck in enumerate(kbinfos["chunks"][:chunks_num]):
        cnt = "\nID: {}".format(i if not hash_id else hash_str2int(get_value(ck, "id", "chunk_id"), 500))
        cnt += draw_node("Title", get_value(ck, "docnm_kwd", "document_name"))
        cnt += draw_node("URL", ck['url']) if "url" in ck else ""
        for k, v in docs.get(get_value(ck, "doc_id", "document_id"), {}).items():
            cnt += draw_node(k, v)
        cnt += "\n└── Content:\n"
        cnt += get_value(ck, "content", "content_with_weight")
        knowledges.append(cnt)

    return knowledges