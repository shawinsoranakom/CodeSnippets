def _fuzzy_match(
    edges_left: pw.Table[Edge],
    edges_right: pw.Table[Edge],
    features: pw.Table[Feature],
    symmetric: bool,
    HEAVY_LIGHT_THRESHOLD,
    by_hand_match: pw.Table[JoinResult] | None = None,
) -> pw.Table[JoinResult]:
    if symmetric:
        assert edges_left is edges_right

    edges_left = edges_left.update_types(
        node=pw.Pointer[Node], feature=pw.Pointer[Feature]
    )
    if not symmetric:
        edges_right = edges_right.update_types(
            node=pw.Pointer[Node], feature=pw.Pointer[Feature]
        )

    if by_hand_match is not None:
        by_hand_match = by_hand_match.update_types(
            left=pw.Pointer[Node], right=pw.Pointer[Node]
        )

    # TODO do a more integrated approach for accommodating by_hand_match.
    if by_hand_match is not None:
        edges_left, edges_right = _filter_out_matched_by_hand(
            edges_left, edges_right, symmetric, by_hand_match
        )

    if symmetric:
        edges = edges_left
        edges_right = edges_right.copy()
    else:
        edges = pw.Table.concat_reindex(edges_left, edges_right)
    features_cnt = features.select(cnt=0).update_rows(
        edges.groupby(id=edges.feature).reduce(cnt=pw.reducers.count())
    )
    del edges

    edges_left_heavy = edges_left.filter(
        features_cnt.ix(edges_left.feature).cnt >= HEAVY_LIGHT_THRESHOLD
    )
    edges_left_light = edges_left.filter(
        features_cnt.ix(edges_left.feature).cnt < HEAVY_LIGHT_THRESHOLD
    )

    if symmetric:
        edges_right_heavy = edges_left_heavy.copy()
        edges_right_light = edges_left_light.copy()
    else:
        edges_right_heavy = edges_right.filter(
            features_cnt.ix(edges_right.feature).cnt >= HEAVY_LIGHT_THRESHOLD
        )
        edges_right_light = edges_right.filter(
            features_cnt.ix(edges_right.feature).cnt < HEAVY_LIGHT_THRESHOLD
        )

    def _normalize_weight(cnt: float, normalization_type: int) -> float:
        return FuzzyJoinNormalization(normalization_type).normalize(cnt)

    features_normalized = features.select(
        weight=features.weight
        * pw.apply(
            _normalize_weight,
            features_cnt.restrict(features).cnt,
            features.normalization_type,
        )
    )
    node_node_light: pw.Table[JoinResult] = edges_left_light.join(
        edges_right_light, edges_left_light.feature == edges_right_light.feature
    ).select(
        weight=edges_left_light.weight
        * edges_right_light.weight
        * features_normalized.ix(pw.this.feature).weight,
        left=edges_left_light.node,
        right=edges_right_light.node,
    )
    if symmetric:
        node_node_light = node_node_light.filter(
            node_node_light.left != node_node_light.right
        )

    node_node_light = node_node_light.groupby(
        node_node_light.left, node_node_light.right
    ).reduce(
        node_node_light.left,
        node_node_light.right,
        weight=pw.reducers.sum(node_node_light.weight),
    )

    node_node_heavy = (
        node_node_light.join(edges_left_heavy, pw.left.left == pw.right.node)
        .join(
            edges_right_heavy,
            pw.left.right == pw.right.node,
            pw.left.feature == pw.right.feature,
        )
        .select(
            pw.this.left,
            pw.this.right,
            weight=edges_left_heavy.weight
            * edges_right_heavy.weight
            * features_normalized.ix(pw.this.feature).weight,
        )
    )

    def weight_to_pseudoweight(weight, left_id, right_id):
        return pw.if_else(
            left_id < right_id,
            pw.make_tuple(weight, left_id, right_id),
            pw.make_tuple(weight, right_id, left_id),
        )

    node_node = (
        pw.Table.concat_reindex(node_node_light, node_node_heavy)
        .groupby(pw.this.left, pw.this.right)
        .reduce(pw.this.left, pw.this.right, weight=pw.reducers.sum(pw.this.weight))
        .with_columns(
            weight=weight_to_pseudoweight(
                pw.this.weight,
                pw.this.left,
                pw.this.right,
            ),
        )
        .groupby(pw.this.left)
        .reduce(
            pw.this.left,
            pw.this.ix(pw.reducers.argmax(pw.this.weight)).right,
            weight=pw.reducers.max(pw.this.weight),
        )
        .groupby(pw.this.right)
        .reduce(
            pw.this.right,
            pw.this.ix(pw.reducers.argmax(pw.this.weight)).left,
            weight=pw.reducers.max(pw.this.weight),
        )
    )

    if symmetric:
        node_node = node_node.filter(node_node.left < node_node.right)

    node_node = node_node.with_columns(
        weight=pw.this.weight[0],
    )

    if by_hand_match is not None:
        node_node = node_node.update_rows(by_hand_match)

    return node_node