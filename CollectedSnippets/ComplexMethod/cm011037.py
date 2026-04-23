def hier_unzip(
    splitter: object,
    layoutA: Layout,
    layoutB: LayoutInput,
) -> Layout:
    if layoutB is None:
        return make_layout(Layout(1, 0), layoutA)
    elif is_tuple(layoutB):
        if len(layoutA) < len(layoutB):
            raise AssertionError
        # A layout with shape ((A,a),(B,b),(C,c))
        split = make_layout(
            hier_unzip(splitter, layoutA[i], layoutB[i])  # type: ignore[arg-type]
            for i in range(len(layoutB))
        )
        # Gather to shape ((A,B,C,...),(a,b,c,...,y,z))
        return make_layout(
            make_layout(split[i][0] for i in range(len(layoutB))),  # type: ignore[arg-type]
            make_layout(
                chain(  # type: ignore[arg-type]
                    (split[i][1] for i in range(len(layoutB))),
                    (layoutA[i] for i in range(len(layoutB), len(layoutA))),
                )
            ),
        )

    # splitter must return a rank-2 layout
    return splitter(layoutA, layoutB)