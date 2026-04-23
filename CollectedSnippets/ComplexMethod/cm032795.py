async def run_toc_from_text(chunks, chat_mdl, callback=None):
    input_budget = int(chat_mdl.max_length * INPUT_UTILIZATION) - num_tokens_from_string(
        TOC_FROM_TEXT_USER + TOC_FROM_TEXT_SYSTEM
    )

    input_budget = 1024 if input_budget > 1024 else input_budget
    chunk_sections = split_chunks(chunks, input_budget)
    titles = []

    chunks_res = []
    tasks = []
    for i, chunk in enumerate(chunk_sections):
        if not chunk:
            continue
        chunks_res.append({"chunks": chunk})
        tasks.append(asyncio.create_task(gen_toc_from_text(chunks_res[-1], chat_mdl, callback)))
    try:
        await asyncio.gather(*tasks, return_exceptions=False)
    except Exception as e:
        logging.error(f"Error generating TOC: {e}")
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        raise

    for chunk in chunks_res:
        titles.extend(chunk.get("toc", []))

    # Filter out entries with title == -1
    prune = len(titles) > 512
    max_len = 12 if prune else 22
    filtered = []
    for x in titles:
        if not isinstance(x, dict) or not x.get("title") or x["title"] == "-1":
            continue
        if len(rag_tokenizer.tokenize(x["title"]).split(" ")) > max_len:
            continue
        if re.match(r"[0-9,.()/ -]+$", x["title"]):
            continue
        filtered.append(x)

    logging.info(f"\n\nFiltered TOC sections:\n{filtered}")
    if not filtered:
        return []

    # Generate initial level (level/title)
    raw_structure = [x.get("title", "") for x in filtered]

    # Assign hierarchy levels using LLM
    toc_with_levels = await assign_toc_levels(raw_structure, chat_mdl, {"temperature": 0.0, "top_p": 0.9})
    if not toc_with_levels:
        return []

    # Merge structure and content (by index)
    prune = len(toc_with_levels) > 512
    max_lvl = "0"
    sorted_list = sorted([t.get("level", "0") for t in toc_with_levels if isinstance(t, dict)])
    if sorted_list:
        max_lvl = sorted_list[-1]
    merged = []
    for _, (toc_item, src_item) in enumerate(zip(toc_with_levels, filtered)):
        if prune and toc_item.get("level", "0") >= max_lvl:
            continue
        merged.append({
            "level": toc_item.get("level", "0"),
            "title": toc_item.get("title", ""),
            "chunk_id": src_item.get("chunk_id", ""),
        })

    return merged