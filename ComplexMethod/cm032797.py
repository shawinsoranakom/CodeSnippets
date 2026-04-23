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