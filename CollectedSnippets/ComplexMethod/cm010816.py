def iter_graph(
        roots: list[torch.autograd.graph.Node],
    ) -> Iterator[torch.autograd.graph.Node]:
        if not roots:
            return
        seen = set()
        q = collections.deque()
        for node in roots:
            if node is not None and node not in seen:
                seen.add(node)
                q.append(node)

        while q:
            node = q.popleft()
            for fn, _idx in node.next_functions:
                if fn in seen or fn is None:
                    continue
                seen.add(fn)
                q.append(fn)

            yield node