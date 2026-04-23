async def relevant_chunks_with_toc(query: str, toc: list[dict], chat_mdl, topn: int = 6):
    import numpy as np
    try:
        ans = await gen_json(
            PROMPT_JINJA_ENV.from_string(TOC_RELEVANCE_SYSTEM).render(),
            PROMPT_JINJA_ENV.from_string(TOC_RELEVANCE_USER).render(query=query, toc_json="[\n%s\n]\n" % "\n".join(
                [json.dumps({"level": d["level"], "title": d["title"]}, ensure_ascii=False) for d in toc])),
            chat_mdl,
            gen_conf={"temperature": 0.0, "top_p": 0.9}
        )
        id2score = {}
        for ti, sc in zip(toc, ans):
            if not isinstance(sc, dict) or sc.get("score", -1) < 1:
                continue
            for id in ti.get("ids", []):
                if id not in id2score:
                    id2score[id] = []
                id2score[id].append(sc["score"] / 5.)
        for id in id2score.keys():
            id2score[id] = np.mean(id2score[id])
        return [(id, sc) for id, sc in list(id2score.items()) if sc >= 0.3][:topn]
    except Exception as e:
        logging.exception(e)
    return []