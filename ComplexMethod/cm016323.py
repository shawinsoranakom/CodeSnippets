def blocks(pf: PythonFile) -> list[Block]:
    blocks: list[Block] = []

    it = (i for i, t in enumerate(pf.tokens) if t.string in ("class", "def"))
    blocks = [_make_block(pf, i) for i in it]

    for i, parent in enumerate(blocks):
        for j in range(i + 1, len(blocks)):
            if parent.contains(child := blocks[j]):
                child.parent = i
                parent.children.append(j)
            else:
                break

    for i, b in enumerate(blocks):
        b.index = i
        parents = [b]
        while (p := parents[-1].parent) is not None:
            parents.append(blocks[p])
        parents = parents[1:]

        b.is_local = not all(p.is_class for p in parents)
        b.is_method = not b.is_class and bool(parents) and parents[0].is_class

    _add_full_names(blocks, [b for b in blocks if b.parent is None])
    return blocks