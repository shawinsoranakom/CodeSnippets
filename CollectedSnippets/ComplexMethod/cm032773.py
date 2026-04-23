async def run_raptor_for_kb(row, kb_parser_config, chat_mdl, embd_mdl, vector_size, callback=None, doc_ids=[]):
    fake_doc_id = GRAPH_RAPTOR_FAKE_DOC_ID

    raptor_config = kb_parser_config.get("raptor", {})
    vctr_nm = "q_%d_vec" % vector_size

    res = []
    tk_count = 0
    max_errors = int(os.environ.get("RAPTOR_MAX_ERRORS", 3))
    doc_name_by_id = {}
    for doc_id in set(doc_ids):
        ok, source_doc = DocumentService.get_by_id(doc_id)
        if not ok or not source_doc:
            continue
        source_name = getattr(source_doc, "name", "")
        if source_name:
            doc_name_by_id[doc_id] = source_name

    async def generate(chunks, did):
        nonlocal tk_count, res
        raptor = Raptor(
            raptor_config.get("max_cluster", 64),
            chat_mdl,
            embd_mdl,
            raptor_config["prompt"],
            raptor_config["max_token"],
            raptor_config["threshold"],
            max_errors=max_errors,
        )
        original_length = len(chunks)
        chunks = await raptor(chunks, kb_parser_config["raptor"]["random_seed"], callback, row["id"])
        effective_doc_name = row["name"] if did == fake_doc_id else doc_name_by_id.get(did, row["name"])
        doc = {
            "doc_id": did,
            "kb_id": [str(row["kb_id"])],
            "docnm_kwd": effective_doc_name,
            "title_tks": rag_tokenizer.tokenize(effective_doc_name),
            "raptor_kwd": "raptor"
        }
        if row["pagerank"]:
            doc[PAGERANK_FLD] = int(row["pagerank"])

        for content, vctr in chunks[original_length:]:
            d = copy.deepcopy(doc)
            d["id"] = xxhash.xxh64((content + str(fake_doc_id)).encode("utf-8")).hexdigest()
            d["create_time"] = str(datetime.now()).replace("T", " ")[:19]
            d["create_timestamp_flt"] = datetime.now().timestamp()
            d[vctr_nm] = vctr.tolist()
            d["content_with_weight"] = content
            d["content_ltks"] = rag_tokenizer.tokenize(content)
            d["content_sm_ltks"] = rag_tokenizer.fine_grained_tokenize(d["content_ltks"])
            res.append(d)
            tk_count += num_tokens_from_string(content)

    if raptor_config.get("scope", "file") == "file":
        for x, doc_id in enumerate(doc_ids):
            # CHECKPOINT: skip docs that already have RAPTOR chunks in the doc store
            if await has_raptor_chunks(doc_id, row["tenant_id"], row["kb_id"]):
                callback(msg=f"[RAPTOR] doc:{doc_id} already has RAPTOR chunks, skipping.")
                callback(prog=(x + 1.) / len(doc_ids))
                continue

            chunks = []
            skipped_chunks = 0
            for d in settings.retriever.chunk_list(doc_id, row["tenant_id"], [str(row["kb_id"])],
                                                   fields=["content_with_weight", vctr_nm],
                                                   sort_by_position=True):
                # Skip chunks that don't have the required vector field (may have been indexed with different embedding model)
                if vctr_nm not in d or d[vctr_nm] is None:
                    skipped_chunks += 1
                    logging.warning(f"RAPTOR: Chunk missing vector field '{vctr_nm}' in doc {doc_id}, skipping")
                    continue
                chunks.append((d["content_with_weight"], np.array(d[vctr_nm])))

            if skipped_chunks > 0:
                callback(msg=f"[WARN] Skipped {skipped_chunks} chunks without vector field '{vctr_nm}' for doc {doc_id}. Consider re-parsing the document with the current embedding model.")

            if not chunks:
                logging.warning(f"RAPTOR: No valid chunks with vectors found for doc {doc_id}")
                callback(msg=f"[WARN] No valid chunks with vectors found for doc {doc_id}, skipping")
                continue

            await generate(chunks, doc_id)
            callback(prog=(x + 1.) / len(doc_ids))
    else:
        chunks = []
        skipped_chunks = 0
        for doc_id in doc_ids:
            for d in settings.retriever.chunk_list(doc_id, row["tenant_id"], [str(row["kb_id"])],
                                                   fields=["content_with_weight", vctr_nm],
                                                   sort_by_position=True):
                # Skip chunks that don't have the required vector field
                if vctr_nm not in d or d[vctr_nm] is None:
                    skipped_chunks += 1
                    logging.warning(f"RAPTOR: Chunk missing vector field '{vctr_nm}' in doc {doc_id}, skipping")
                    continue
                chunks.append((d["content_with_weight"], np.array(d[vctr_nm])))

        if skipped_chunks > 0:
            callback(msg=f"[WARN] Skipped {skipped_chunks} chunks without vector field '{vctr_nm}'. Consider re-parsing documents with the current embedding model.")

        if not chunks:
            logging.error(f"RAPTOR: No valid chunks with vectors found in any document for kb {row['kb_id']}")
            callback(msg=f"[ERROR] No valid chunks with vectors found. Please ensure documents are parsed with the current embedding model (vector size: {vector_size}).")
            return res, tk_count

        await generate(chunks, fake_doc_id)

    return res, tk_count