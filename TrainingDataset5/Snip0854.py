def bfs(g, s):
    vis, q = {s}, deque([s])
    print(s)
    while q:
        u = q.popleft()
        for v in g[u]:
            if v not in vis:
                vis.add(v)
                q.append(v)
                print(v)
