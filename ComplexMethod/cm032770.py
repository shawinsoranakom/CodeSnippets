def build_TOC(task, docs, progress_callback):
    progress_callback(msg="Start to generate table of content ...")
    chat_model_config = get_model_config_by_type_and_name(task["tenant_id"], LLMType.CHAT, task["llm_id"])
    chat_mdl = LLMBundle(task["tenant_id"], chat_model_config, lang=task["language"])
    docs = sorted(docs, key=lambda d: (
        d.get("page_num_int", 0)[0] if isinstance(d.get("page_num_int", 0), list) else d.get("page_num_int", 0),
        d.get("top_int", 0)[0] if isinstance(d.get("top_int", 0), list) else d.get("top_int", 0)
    ))
    toc: list[dict] = asyncio.run(
        run_toc_from_text([d["content_with_weight"] for d in docs], chat_mdl, progress_callback))
    logging.info("------------ T O C -------------\n" + json.dumps(toc, ensure_ascii=False, indent='  '))
    for ii, item in enumerate(toc):
        try:
            chunk_val = item.pop("chunk_id", None)
            if chunk_val is None or str(chunk_val).strip() == "":
                logging.warning(f"Index {ii}: chunk_id is missing or empty. Skipping.")
                continue
            curr_idx = int(chunk_val)
            if curr_idx >= len(docs):
                logging.error(f"Index {ii}: chunk_id {curr_idx} exceeds docs length {len(docs)}.")
                continue
            item["ids"] = [docs[curr_idx]["id"]]
            if ii + 1 < len(toc):
                next_chunk_val = toc[ii + 1].get("chunk_id", "")
                if str(next_chunk_val).strip() != "":
                    next_idx = int(next_chunk_val)
                    for jj in range(curr_idx + 1, min(next_idx + 1, len(docs))):
                        item["ids"].append(docs[jj]["id"])
                else:
                    logging.warning(f"Index {ii + 1}: next chunk_id is empty, range fill skipped.")
        except (ValueError, TypeError) as e:
            logging.error(f"Index {ii}: Data conversion error - {e}")
        except Exception as e:
            logging.exception(f"Index {ii}: Unexpected error - {e}")

    if toc:
        d = copy.deepcopy(docs[-1])
        d["content_with_weight"] = json.dumps(toc, ensure_ascii=False)
        d["toc_kwd"] = "toc"
        d["available_int"] = 0
        d["page_num_int"] = [100000000]
        d["id"] = xxhash.xxh64(
            (d["content_with_weight"] + str(d["doc_id"])).encode("utf-8", "surrogatepass")).hexdigest()
        return d
    return None