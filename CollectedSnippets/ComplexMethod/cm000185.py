def longest_distance(graph):
    indegree = [0] * len(graph)
    queue = []
    long_dist = [1] * len(graph)

    for values in graph.values():
        for i in values:
            indegree[i] += 1

    for i in range(len(indegree)):
        if indegree[i] == 0:
            queue.append(i)

    while queue:
        vertex = queue.pop(0)
        for x in graph[vertex]:
            indegree[x] -= 1

            long_dist[x] = max(long_dist[x], long_dist[vertex] + 1)

            if indegree[x] == 0:
                queue.append(x)

    print(max(long_dist))