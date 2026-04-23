def strong_connect(v: int, index: int, components: list[list[int]]) -> int:
        index_of[v] = index  # the number when this node is seen
        lowlink_of[v] = index  # lowest rank node reachable from here
        index += 1
        stack.append(v)
        on_stack[v] = True

        for w in g[v]:
            if index_of[w] == -1:
                index = strong_connect(w, index, components)
                lowlink_of[v] = (
                    lowlink_of[w] if lowlink_of[w] < lowlink_of[v] else lowlink_of[v]
                )
            elif on_stack[w]:
                lowlink_of[v] = (
                    lowlink_of[w] if lowlink_of[w] < lowlink_of[v] else lowlink_of[v]
                )

        if lowlink_of[v] == index_of[v]:
            component = []
            w = stack.pop()
            on_stack[w] = False
            component.append(w)
            while w != v:
                w = stack.pop()
                on_stack[w] = False
                component.append(w)
            components.append(component)
        return index