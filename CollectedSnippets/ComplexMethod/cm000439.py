async def get_accuracy_trends_and_alerts(
    graph_id: str,
    days_back: int = 30,
    user_id: Optional[str] = None,
    drop_threshold: float = 10.0,
    include_historical: bool = False,
) -> AccuracyTrendsResponse:
    """Get accuracy trends and detect alerts for a specific graph."""
    query_template = """
    WITH daily_scores AS (
        SELECT 
            DATE(e."createdAt") as execution_date,
            AVG(CASE 
                WHEN e.stats IS NOT NULL 
                AND e.stats::json->>'correctness_score' IS NOT NULL
                AND e.stats::json->>'correctness_score' != 'null'
                THEN (e.stats::json->>'correctness_score')::float * 100
                ELSE NULL 
            END) as daily_score
        FROM {schema_prefix}"AgentGraphExecution" e
        WHERE e."agentGraphId" = $1::text
            AND e."isDeleted" = false
            AND e."createdAt" >= $2::timestamp
            AND e."executionStatus" IN ('COMPLETED', 'FAILED', 'TERMINATED')
            {user_filter}
        GROUP BY DATE(e."createdAt")
        HAVING COUNT(*) >= 1  -- Include all days with at least 1 execution
    ),
    trends AS (
        SELECT 
            execution_date,
            daily_score,
            AVG(daily_score) OVER (
                ORDER BY execution_date 
                ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
            ) as three_day_avg,
            AVG(daily_score) OVER (
                ORDER BY execution_date 
                ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
            ) as seven_day_avg,
            AVG(daily_score) OVER (
                ORDER BY execution_date 
                ROWS BETWEEN 13 PRECEDING AND CURRENT ROW
            ) as fourteen_day_avg
        FROM daily_scores
    )
    SELECT *,
        CASE 
            WHEN three_day_avg IS NOT NULL AND seven_day_avg IS NOT NULL AND seven_day_avg > 0
            THEN ((seven_day_avg - three_day_avg) / seven_day_avg * 100)
            ELSE NULL
        END as drop_percent
    FROM trends
    ORDER BY execution_date DESC
    {limit_clause}
    """

    start_date = datetime.now(timezone.utc) - timedelta(days=days_back)
    params = [graph_id, start_date]
    user_filter = ""
    if user_id:
        user_filter = 'AND e."userId" = $3::text'
        params.append(user_id)

    # Determine limit clause
    limit_clause = "" if include_historical else "LIMIT 1"

    final_query = query_template.format(
        schema_prefix="{schema_prefix}",
        user_filter=user_filter,
        limit_clause=limit_clause,
    )

    result = await query_raw_with_schema(final_query, *params)

    if not result:
        return AccuracyTrendsResponse(
            latest_data=AccuracyLatestData(
                date=datetime.now(timezone.utc),
                daily_score=None,
                three_day_avg=None,
                seven_day_avg=None,
                fourteen_day_avg=None,
            ),
            alert=None,
        )

    latest = result[0]

    alert = None
    if (
        latest["drop_percent"] is not None
        and latest["drop_percent"] >= drop_threshold
        and latest["three_day_avg"] is not None
        and latest["seven_day_avg"] is not None
    ):
        alert = AccuracyAlertData(
            graph_id=graph_id,
            user_id=user_id,
            drop_percent=float(latest["drop_percent"]),
            three_day_avg=float(latest["three_day_avg"]),
            seven_day_avg=float(latest["seven_day_avg"]),
            detected_at=datetime.now(timezone.utc),
        )

    # Prepare historical data if requested
    historical_data = None
    if include_historical:
        historical_data = []
        for row in result:
            historical_data.append(
                AccuracyLatestData(
                    date=row["execution_date"],
                    daily_score=(
                        float(row["daily_score"])
                        if row["daily_score"] is not None
                        else None
                    ),
                    three_day_avg=(
                        float(row["three_day_avg"])
                        if row["three_day_avg"] is not None
                        else None
                    ),
                    seven_day_avg=(
                        float(row["seven_day_avg"])
                        if row["seven_day_avg"] is not None
                        else None
                    ),
                    fourteen_day_avg=(
                        float(row["fourteen_day_avg"])
                        if row["fourteen_day_avg"] is not None
                        else None
                    ),
                )
            )

    return AccuracyTrendsResponse(
        latest_data=AccuracyLatestData(
            date=latest["execution_date"],
            daily_score=(
                float(latest["daily_score"])
                if latest["daily_score"] is not None
                else None
            ),
            three_day_avg=(
                float(latest["three_day_avg"])
                if latest["three_day_avg"] is not None
                else None
            ),
            seven_day_avg=(
                float(latest["seven_day_avg"])
                if latest["seven_day_avg"] is not None
                else None
            ),
            fourteen_day_avg=(
                float(latest["fourteen_day_avg"])
                if latest["fourteen_day_avg"] is not None
                else None
            ),
        ),
        alert=alert,
        historical_data=historical_data,
    )