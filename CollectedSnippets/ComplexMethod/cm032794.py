async def table_of_contents_index(toc_arr: list[dict], sections: list[str], chat_mdl):
    if not toc_arr or not sections:
        return []

    toc_map = {}
    for i, it in enumerate(toc_arr):
        k1 = (it["structure"] + it["title"]).replace(" ", "")
        k2 = it["title"].strip()
        if k1 not in toc_map:
            toc_map[k1] = []
        if k2 not in toc_map:
            toc_map[k2] = []
        toc_map[k1].append(i)
        toc_map[k2].append(i)

    for it in toc_arr:
        it["indices"] = []
    for i, sec in enumerate(sections):
        sec = sec.strip()
        if sec.replace(" ", "") in toc_map:
            for j in toc_map[sec.replace(" ", "")]:
                toc_arr[j]["indices"].append(i)

    all_pathes = []

    def dfs(start, path):
        nonlocal all_pathes
        if start >= len(toc_arr):
            if path:
                all_pathes.append(path)
            return
        if not toc_arr[start]["indices"]:
            dfs(start + 1, path)
            return
        added = False
        for j in toc_arr[start]["indices"]:
            if path and j < path[-1][0]:
                continue
            _path = deepcopy(path)
            _path.append((j, start))
            added = True
            dfs(start + 1, _path)
        if not added and path:
            all_pathes.append(path)

    dfs(0, [])
    path = max(all_pathes, key=lambda x: len(x))
    for it in toc_arr:
        it["indices"] = []
    for j, i in path:
        toc_arr[i]["indices"] = [j]
    print(json.dumps(toc_arr, ensure_ascii=False, indent=2))

    i = 0
    while i < len(toc_arr):
        it = toc_arr[i]
        if it["indices"]:
            i += 1
            continue

        if i > 0 and toc_arr[i - 1]["indices"]:
            st_i = toc_arr[i - 1]["indices"][-1]
        else:
            st_i = 0
        e = i + 1
        while e < len(toc_arr) and not toc_arr[e]["indices"]:
            e += 1
        if e >= len(toc_arr):
            e = len(sections)
        else:
            e = toc_arr[e]["indices"][0]

        for j in range(st_i, min(e + 1, len(sections))):
            ans = await gen_json(PROMPT_JINJA_ENV.from_string(TOC_INDEX).render(
                structure=it["structure"],
                title=it["title"],
                text=sections[j]), "Only JSON please.", chat_mdl)
            if ans["exist"] == "yes":
                it["indices"].append(j)
                break

        i += 1

    return toc_arr