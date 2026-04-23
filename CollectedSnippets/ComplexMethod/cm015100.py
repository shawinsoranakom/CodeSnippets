def iter_graph(roots):
            if not roots:
                return
            seen = set()
            q = collections.deque()
            for node in roots:
                if node is not None:
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