def fuzzy_match_tables(
    left_table: pw.Table,
    right_table: pw.Table,
    *,
    by_hand_match: pw.Table[JoinResult] | None = None,
    normalization=FuzzyJoinNormalization.LOGWEIGHT,
    feature_generation=FuzzyJoinFeatureGeneration.AUTO,
    left_projection: dict[str, str] = {},
    right_projection: dict[str, str] = {},
) -> pw.Table[JoinResult]:
    # If one projection is empty, we don't do any projection fuzzy_match_tables
    if left_projection == {} or right_projection == {}:
        return _fuzzy_match_tables(
            left_table=left_table,
            right_table=right_table,
            by_hand_match=by_hand_match,
            normalization=normalization,
            feature_generation=feature_generation,
        )

    # We compute the projections spaces and for each bucket b we keep track of the
    # corresponding columns which are projected into b.
    set_buckets: StableSet[str] = StableSet()
    buckets_left: dict[str, list] = {}
    buckets_right: dict[str, list] = {}

    for col_name in left_table._columns.keys():
        if col_name not in left_projection:
            continue
        bucket_id = left_projection[col_name]
        set_buckets.add(bucket_id)
        if bucket_id not in buckets_left:
            buckets_left[bucket_id] = []
        buckets_left[bucket_id].append(col_name)

    for col_name in right_table._columns.keys():
        if col_name not in right_projection:
            continue
        bucket_id = right_projection[col_name]
        set_buckets.add(bucket_id)
        if bucket_id not in buckets_right:
            buckets_right[bucket_id] = []
        buckets_right[bucket_id].append(col_name)

    # For each bucket, we compute the fuzzy_match_table on the table only with
    # the columns associated to the bucket.
    # The corresponding matches are then added in a common 'matchings' columns
    fuzzy_match_bucket_list = []
    for bucket_id in set_buckets:
        left_table_bucket = left_table[buckets_left[bucket_id]]

        right_table_bucket = right_table[buckets_right[bucket_id]]

        fuzzy_match_bucket = _fuzzy_match_tables(
            left_table=left_table_bucket,
            right_table=right_table_bucket,
            by_hand_match=by_hand_match,
            normalization=normalization,
            feature_generation=feature_generation,
        )
        fuzzy_match_bucket_list.append(fuzzy_match_bucket)
    matchings = pw.Table.concat_reindex(*fuzzy_match_bucket_list)

    # Matchings are grouped by left/right pairs and the weights are summed.
    matchings = matchings.groupby(matchings.left, matchings.right).reduce(
        matchings.left,
        matchings.right,
        weight=pw.reducers.sum(matchings.weight),
    )
    return matchings