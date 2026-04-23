def search_optimizer(
    query,
    proxies,
    history,
    llm_kwargs,
    optimizer=1,
    categories="general",
    searxng_url=None,
    engines=None,
):
    # ------------- < 第1步：尝试进行搜索优化 > -------------
    # * 增强优化，会尝试结合历史记录进行搜索优化
    if optimizer == 2:
        his = " "
        if len(history) == 0:
            pass
        else:
            for i, h in enumerate(history):
                if i % 2 == 0:
                    his += f"Q: {h}\n"
                else:
                    his += f"A: {h}\n"
        if categories == "general":
            sys_prompt = SearchOptimizerPrompt.format(query=query, history=his, num=4)
        elif categories == "science":
            sys_prompt = SearchAcademicOptimizerPrompt.format(query=query, history=his, num=4)
    else:
        his = " "
        if categories == "general":
            sys_prompt = SearchOptimizerPrompt.format(query=query, history=his, num=3)
        elif categories == "science":
            sys_prompt = SearchAcademicOptimizerPrompt.format(query=query, history=his, num=3)

    mutable = ["", time.time(), ""]
    llm_kwargs["temperature"] = 0.8
    try:
        query_json = predict_no_ui_long_connection(
            inputs=query,
            llm_kwargs=llm_kwargs,
            history=[],
            sys_prompt=sys_prompt,
            observe_window=mutable,
        )
    except Exception:
        query_json = "null"
    #* 尝试解码优化后的搜索结果
    query_json = re.sub(r"```json|```", "", query_json)
    try:
        queries = json.loads(query_json)
    except Exception:
        #* 如果解码失败,降低温度再试一次
        try:
            llm_kwargs["temperature"] = 0.4
            query_json = predict_no_ui_long_connection(
                inputs=query,
                llm_kwargs=llm_kwargs,
                history=[],
                sys_prompt=sys_prompt,
                observe_window=mutable,
            )
            query_json = re.sub(r"```json|```", "", query_json)
            queries = json.loads(query_json)
        except Exception:
            #* 如果再次失败，直接返回原始问题
            queries = [query]
    links = []
    success = 0
    Exceptions = ""
    for q in queries:
        try:
            link = searxng_request(q, proxies, categories, searxng_url, engines=engines)
            if len(link) > 0:
                links.append(link[:-5])
                success += 1
        except Exception:
            Exceptions = Exception
            pass
    if success == 0:
        raise ValueError(f"在线搜索失败！\n{Exceptions}")
    # * 清洗搜索结果，依次放入每组第一，第二个搜索结果，并清洗重复的搜索结果
    seen_links = set()
    result = []
    for tuple in zip_longest(*links, fillvalue=None):
        for item in tuple:
            if item is not None:
                link = item["link"]
                if link not in seen_links:
                    seen_links.add(link)
                    result.append(item)
    return result