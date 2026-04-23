def astar(world, start, goal):
    """
    Implementation of a start algorithm.
    world : Object of the world object.
    start : Object of the cell as  start position.
    stop  : Object of the cell as goal position.

    >>> p = Gridworld()
    >>> start = Cell()
    >>> start.position = (0,0)
    >>> goal = Cell()
    >>> goal.position = (4,4)
    >>> astar(p, start, goal)
    [(0, 0), (1, 1), (2, 2), (3, 3), (4, 4)]
    """
    _open = []
    _closed = []
    _open.append(start)

    while _open:
        min_f = np.argmin([n.f for n in _open])
        current = _open[min_f]
        _closed.append(_open.pop(min_f))
        if current == goal:
            break
        for n in world.get_neighbours(current):
            for c in _closed:
                if c == n:
                    continue
            n.g = current.g + 1
            x1, y1 = n.position
            x2, y2 = goal.position
            n.h = (y2 - y1) ** 2 + (x2 - x1) ** 2
            n.f = n.h + n.g

            for c in _open:
                if c == n and c.f < n.f:
                    continue
            _open.append(n)
    path = []
    while current.parent is not None:
        path.append(current.position)
        current = current.parent
    path.append(current.position)
    return path[::-1]