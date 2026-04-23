def earclip_triangulation(verts: Vect3Array | Vect2Array, ring_ends: list[int]) -> list[int]:
    """
    Returns a list of indices giving a triangulation
    of a polygon, potentially with holes

    - verts is a numpy array of points

    - ring_ends is a list of indices indicating where
    the ends of new paths are
    """

    rings = [
        list(range(e0, e1))
        for e0, e1 in zip([0, *ring_ends], ring_ends)
    ]
    epsilon = 1e-6

    def is_in(point, ring_id):
        return abs(abs(get_winding_number([i - point for i in verts[rings[ring_id]]])) - 1) < epsilon

    def ring_area(ring_id):
        ring = rings[ring_id]
        s = 0
        for i, j in zip(ring[1:], ring):
            s += cross2d(verts[i], verts[j])
        return abs(s) / 2

    # Points at the same position may cause problems
    for i in rings:
        if len(i) < 2:
            continue
        verts[i[0]] += (verts[i[1]] - verts[i[0]]) * epsilon
        verts[i[-1]] += (verts[i[-2]] - verts[i[-1]]) * epsilon

    # First, we should know which rings are directly contained in it for each ring

    right = [max(verts[rings[i], 0]) for i in range(len(rings))]
    left = [min(verts[rings[i], 0]) for i in range(len(rings))]
    top = [max(verts[rings[i], 1]) for i in range(len(rings))]
    bottom = [min(verts[rings[i], 1]) for i in range(len(rings))]
    area = [ring_area(i) for i in range(len(rings))]

    # The larger ring must be outside
    rings_sorted = list(range(len(rings)))
    rings_sorted.sort(key=lambda x: area[x], reverse=True)

    def is_in_fast(ring_a, ring_b):
        # Whether a is in b
        return reduce(op.and_, (
            left[ring_b] <= left[ring_a] <= right[ring_a] <= right[ring_b],
            bottom[ring_b] <= bottom[ring_a] <= top[ring_a] <= top[ring_b],
            is_in(verts[rings[ring_a][0]], ring_b)
        ))

    chilren = [[] for i in rings]
    ringenum = ProgressDisplay(
        enumerate(rings_sorted),
        total=len(rings),
        leave=False,
        ascii=True if platform.system() == 'Windows' else None,
        dynamic_ncols=True,
        desc="SVG Triangulation",
        delay=3,
    )
    for idx, i in ringenum:
        for j in rings_sorted[:idx][::-1]:
            if is_in_fast(i, j):
                chilren[j].append(i)
                break

    res = []

    # Then, we can use earcut for each part
    used = [False] * len(rings)
    for i in rings_sorted:
        if used[i]:
            continue
        v = rings[i]
        ring_ends = [len(v)]
        for j in chilren[i]:
            used[j] = True
            v += rings[j]
            ring_ends.append(len(v))
        res += [v[i] for i in earcut(verts[v, :2], ring_ends)]

    return res