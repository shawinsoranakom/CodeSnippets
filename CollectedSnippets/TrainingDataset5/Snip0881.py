def breadth_first_search(graph: dict, start: str) -> list[str]:
    explored = {start}
    result = [start]
    queue: Queue = Queue()
    queue.put(start)
    while not queue.empty():
        v = queue.get()
        for w in graph[v]:
            if w not in explored:
                explored.add(w)
                result.append(w)
                queue.put(w)
    return result
