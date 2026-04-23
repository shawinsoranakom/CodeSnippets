def iter_graph(roots: list[Node]) -> Iterator[Node]:
        if not roots:
            return
        seen: set[Node] = set()
        q: deque[Node] = deque()
        for node in roots:
            if node is not None:
                seen.add(node)
                q.append(node)

        while q:
            node = q.popleft()
            for fn, _ in node.next_functions:
                if fn in seen or fn is None:
                    continue
                seen.add(fn)
                q.append(fn)

            yield node