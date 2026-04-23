def _generate_get_metadata_stmt(
    statistic_ids: set[str] | None = None,
    statistic_type: Literal["mean", "sum"] | None = None,
    statistic_source: str | None = None,
    schema_version: int = 0,
) -> StatementLambdaElement:
    """Generate a statement to fetch metadata with the passed filters.

    Depending on the schema version, either mean_type (added in version 49) or has_mean column is used.
    """
    columns: list[InstrumentedAttribute[Any]] = list(QUERY_STATISTICS_META)
    if schema_version >= CIRCULAR_MEAN_SCHEMA_VERSION:
        columns.append(StatisticsMeta.mean_type)
    else:
        columns.append(StatisticsMeta.has_mean)
    if schema_version >= UNIT_CLASS_SCHEMA_VERSION:
        columns.append(StatisticsMeta.unit_class)
    stmt = lambda_stmt(lambda: select(*columns))
    if statistic_ids:
        stmt += lambda q: q.where(StatisticsMeta.statistic_id.in_(statistic_ids))
    if statistic_source is not None:
        stmt += lambda q: q.where(StatisticsMeta.source == statistic_source)
    if statistic_type == "mean":
        if schema_version >= CIRCULAR_MEAN_SCHEMA_VERSION:
            stmt += lambda q: q.where(
                StatisticsMeta.mean_type != StatisticMeanType.NONE
            )
        else:
            stmt += lambda q: q.where(StatisticsMeta.has_mean == true())
    elif statistic_type == "sum":
        stmt += lambda q: q.where(StatisticsMeta.has_sum == true())
    return stmt