def dijk(g, s):
    dist, known, path = {s: 0}, set(), {s: 0}
    while True:
        if len(known) == len(g) - 1:
            break
        mini = 100000
        for key, value in dist:
            if key not in known and value < mini:
                mini = value
                u = key
        known.add(u)
        for v in g[u]:
            if v[0] not in known and dist[u] + v[1] < dist.get(v[0], 100000):
                dist[v[0]] = dist[u] + v[1]
                path[v[0]] = u
    for key, value in dist.items():
        if key != s:
            print(value)
