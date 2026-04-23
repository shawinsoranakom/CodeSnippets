async def get_platform_cost_dashboard(
    start: datetime | None = None,
    end: datetime | None = None,
    provider: str | None = None,
    user_id: str | None = None,
    model: str | None = None,
    block_name: str | None = None,
    tracking_type: str | None = None,
    graph_exec_id: str | None = None,
) -> PlatformCostDashboard:
    """Aggregate platform cost logs for the admin dashboard.

    Note: by_provider rows are keyed on (provider, tracking_type). A single
    provider can therefore appear in multiple rows if it has entries with
    different billing models (e.g. "openai" with both "tokens" and "cost_usd"
    if pricing is later added for some entries). Frontend treats each row
    independently rather than as a provider primary key.

    Defaults to the last DEFAULT_DASHBOARD_DAYS days when no start date is
    provided to avoid full-table scans on large deployments.
    """
    if start is None:
        start = datetime.now(timezone.utc) - timedelta(days=DEFAULT_DASHBOARD_DAYS)

    where = _build_prisma_where(
        start, end, provider, user_id, model, block_name, tracking_type, graph_exec_id
    )

    # For per-user tracking-type breakdown we intentionally omit the
    # tracking_type filter so cost_usd and tokens rows are always present.
    # This ensures cost_bearing_request_count is correct even when the caller
    # is filtering the main view by a different tracking_type.
    where_no_tracking_type = _build_prisma_where(
        start,
        end,
        provider,
        user_id,
        model,
        block_name,
        tracking_type=None,
        graph_exec_id=graph_exec_id,
    )

    sum_fields = {
        "costMicrodollars": True,
        "inputTokens": True,
        "outputTokens": True,
        "cacheReadTokens": True,
        "cacheCreationTokens": True,
        "duration": True,
        "trackingAmount": True,
    }

    # Build parameterised WHERE clause for the raw SQL percentile/bucket
    # queries.  Uses _build_raw_where so filter logic is shared with
    # _build_prisma_where and only maintained in one place.
    # Always force tracking_type=None here so _build_raw_where defaults to
    # "cost_usd" — percentile and histogram queries only make sense on
    # cost-denominated rows, regardless of what the caller is filtering.
    raw_where, raw_params = _build_raw_where(
        start,
        end,
        provider,
        user_id,
        model,
        block_name,
        tracking_type=None,
        graph_exec_id=graph_exec_id,
    )

    # Queries that always run regardless of tracking_type filter.
    common_queries = [
        # (provider, trackingType, model) aggregation — no ORDER BY in ORM;
        # sort by total cost descending in Python after fetch.
        PrismaLog.prisma().group_by(
            by=["provider", "trackingType", "model"],
            where=where,
            sum=sum_fields,
            count=True,
        ),
        # userId aggregation — emails fetched separately below.
        PrismaLog.prisma().group_by(
            by=["userId"],
            where=where,
            sum=sum_fields,
            count=True,
        ),
        # Per-user cost-bearing request count: group by (userId, trackingType)
        # so we can compute the correct denominator for per-user avg cost.
        # Uses where_no_tracking_type so cost_usd rows are always included
        # even when the caller filters the main view by a different tracking_type.
        PrismaLog.prisma().group_by(
            by=["userId", "trackingType"],
            where=where_no_tracking_type,
            count=True,
        ),
        # Distinct user count: group by userId, count groups.
        PrismaLog.prisma().group_by(
            by=["userId"],
            where=where,
            count=True,
        ),
        # Total aggregate (filtered): group by (provider, trackingType) so we can
        # compute cost-bearing and token-bearing denominators for avg stats.
        PrismaLog.prisma().group_by(
            by=["provider", "trackingType"],
            where=where,
            sum={
                "costMicrodollars": True,
                "inputTokens": True,
                "outputTokens": True,
            },
            count=True,
        ),
        # Percentile distribution of cost per request (respects all filters).
        query_raw_with_schema(
            "SELECT"
            "  percentile_cont(0.5) WITHIN GROUP"
            '    (ORDER BY "costMicrodollars") as p50,'
            "  percentile_cont(0.75) WITHIN GROUP"
            '    (ORDER BY "costMicrodollars") as p75,'
            "  percentile_cont(0.95) WITHIN GROUP"
            '    (ORDER BY "costMicrodollars") as p95,'
            "  percentile_cont(0.99) WITHIN GROUP"
            '    (ORDER BY "costMicrodollars") as p99'
            ' FROM {schema_prefix}"PlatformCostLog"'
            f" WHERE {raw_where}",
            *raw_params,
        ),
        # Histogram buckets for cost distribution (respects all filters).
        # NULL costMicrodollars is excluded explicitly to prevent such rows
        # from falling through all WHEN clauses into the ELSE '$10+' bucket.
        query_raw_with_schema(
            "SELECT"
            "  CASE"
            '    WHEN "costMicrodollars" < 500000'
            "      THEN '$0-0.50'"
            '    WHEN "costMicrodollars" < 1000000'
            "      THEN '$0.50-1'"
            '    WHEN "costMicrodollars" < 2000000'
            "      THEN '$1-2'"
            '    WHEN "costMicrodollars" < 5000000'
            "      THEN '$2-5'"
            '    WHEN "costMicrodollars" < 10000000'
            "      THEN '$5-10'"
            "    ELSE '$10+'"
            "  END as bucket,"
            "  COUNT(*) as count"
            ' FROM {schema_prefix}"PlatformCostLog"'
            f' WHERE {raw_where} AND "costMicrodollars" IS NOT NULL'
            " GROUP BY bucket"
            ' ORDER BY MIN("costMicrodollars")',
            *raw_params,
        ),
    ]

    # Only run the unfiltered aggregate query when tracking_type is set;
    # when tracking_type is None, the filtered query already contains all
    # tracking types and reusing it avoids a redundant full aggregation.
    if tracking_type is not None:
        common_queries.append(
            # Total aggregate (no tracking_type filter): used to compute
            # cost_bearing_requests and token_bearing_requests denominators so
            # global avg stats remain meaningful when the caller filters the
            # main view by a specific tracking_type (e.g. 'tokens').
            PrismaLog.prisma().group_by(
                by=["provider", "trackingType"],
                where=where_no_tracking_type,
                sum={
                    "costMicrodollars": True,
                    "inputTokens": True,
                    "outputTokens": True,
                },
                count=True,
            )
        )

    results = await asyncio.gather(*common_queries)

    # Unpack results by name for clarity.
    by_provider_groups = results[0]
    by_user_groups = results[1]
    by_user_tracking_groups = results[2]
    total_user_groups = results[3]
    total_agg_groups = results[4]
    percentile_rows = results[5]
    bucket_rows = results[6]
    # When tracking_type is None, the filtered and unfiltered queries are
    # identical — reuse total_agg_groups to avoid the extra DB round-trip.
    total_agg_no_tracking_type_groups = (
        results[7] if tracking_type is not None else total_agg_groups
    )

    # Compute token grand-totals from the unfiltered aggregate so they remain
    # consistent with the avg-token stats (which also use unfiltered data).
    # Using by_provider_groups here would give 0 tokens when tracking_type='cost_usd'
    # because cost_usd rows carry no token data, contradicting non-zero averages.
    total_input_tokens = sum(
        _si(r, "inputTokens")
        for r in total_agg_no_tracking_type_groups
        if r.get("trackingType") == "tokens"
    )
    total_output_tokens = sum(
        _si(r, "outputTokens")
        for r in total_agg_no_tracking_type_groups
        if r.get("trackingType") == "tokens"
    )

    # Sort by_provider by total cost descending and cap at MAX_PROVIDER_ROWS.
    by_provider_groups.sort(key=lambda r: _si(r, "costMicrodollars"), reverse=True)
    by_provider_groups = by_provider_groups[:MAX_PROVIDER_ROWS]

    # Sort by_user by total cost descending and cap at MAX_USER_ROWS.
    by_user_groups.sort(key=lambda r: _si(r, "costMicrodollars"), reverse=True)
    by_user_groups = by_user_groups[:MAX_USER_ROWS]

    # Batch-fetch emails for the users in by_user.
    user_ids = [r["userId"] for r in by_user_groups if r.get("userId") is not None]
    email_by_user_id: dict[str, str | None] = {}
    if user_ids:
        users = await PrismaUser.prisma().find_many(
            where={"id": {"in": user_ids}},
        )
        email_by_user_id = {u.id: u.email for u in users}

    # Total distinct users — exclude the NULL-userId group (deleted users).
    total_users = len([g for g in total_user_groups if g.get("userId") is not None])

    # Grand totals — sum across all provider groups (no LIMIT applied above).
    total_cost = sum(_si(r, "costMicrodollars") for r in total_agg_groups)
    total_requests = sum(_ca(r) for r in total_agg_groups)

    # Extract percentile values from the raw query result.
    pctl = percentile_rows[0] if percentile_rows else {}
    cost_p50 = float(pctl.get("p50") or 0)
    cost_p75 = float(pctl.get("p75") or 0)
    cost_p95 = float(pctl.get("p95") or 0)
    cost_p99 = float(pctl.get("p99") or 0)

    # Build cost bucket list.
    cost_buckets: list[CostBucket] = [
        CostBucket(bucket=r["bucket"], count=int(r["count"])) for r in bucket_rows
    ]

    # Avg-stat numerators and denominators are derived from the unfiltered
    # aggregate so they remain meaningful when the caller filters by a specific
    # tracking_type.  Example: filtering by 'tokens' excludes cost_usd rows from
    # total_agg_groups, so avg_cost would always be 0 if we used that; using
    # total_agg_no_tracking_type_groups gives the correct cost_usd total/count.
    avg_cost_total = sum(
        _si(r, "costMicrodollars")
        for r in total_agg_no_tracking_type_groups
        if r.get("trackingType") == "cost_usd"
    )
    cost_bearing_requests = sum(
        _ca(r)
        for r in total_agg_no_tracking_type_groups
        if r.get("trackingType") == "cost_usd"
    )
    avg_input_total = sum(
        _si(r, "inputTokens")
        for r in total_agg_no_tracking_type_groups
        if r.get("trackingType") == "tokens"
    )
    avg_output_total = sum(
        _si(r, "outputTokens")
        for r in total_agg_no_tracking_type_groups
        if r.get("trackingType") == "tokens"
    )
    # Token-bearing request count: only rows where trackingType == "tokens".
    # Token averages must use this denominator; cost_usd rows do not carry tokens.
    token_bearing_requests = sum(
        _ca(r)
        for r in total_agg_no_tracking_type_groups
        if r.get("trackingType") == "tokens"
    )

    # Per-user cost-bearing request count: used for per-user avg cost so the
    # denominator matches the numerator (cost_usd rows only, per user).
    user_cost_bearing_counts: dict[str, int] = {}
    for r in by_user_tracking_groups:
        if r.get("trackingType") == "cost_usd" and r.get("userId"):
            uid = r["userId"]
            user_cost_bearing_counts[uid] = user_cost_bearing_counts.get(uid, 0) + _ca(
                r
            )

    return PlatformCostDashboard(
        by_provider=[
            ProviderCostSummary(
                provider=r["provider"],
                tracking_type=r.get("trackingType"),
                model=r.get("model"),
                total_cost_microdollars=_si(r, "costMicrodollars"),
                total_input_tokens=_si(r, "inputTokens"),
                total_output_tokens=_si(r, "outputTokens"),
                total_cache_read_tokens=_si(r, "cacheReadTokens"),
                total_cache_creation_tokens=_si(r, "cacheCreationTokens"),
                total_duration_seconds=_sf(r, "duration"),
                total_tracking_amount=_sf(r, "trackingAmount"),
                request_count=_ca(r),
            )
            for r in by_provider_groups
        ],
        by_user=[
            UserCostSummary(
                user_id=r.get("userId"),
                email=_mask_email(email_by_user_id.get(r.get("userId") or "")),
                total_cost_microdollars=_si(r, "costMicrodollars"),
                total_input_tokens=_si(r, "inputTokens"),
                total_output_tokens=_si(r, "outputTokens"),
                total_cache_read_tokens=_si(r, "cacheReadTokens"),
                total_cache_creation_tokens=_si(r, "cacheCreationTokens"),
                request_count=_ca(r),
                cost_bearing_request_count=user_cost_bearing_counts.get(
                    r.get("userId") or "", 0
                ),
            )
            for r in by_user_groups
        ],
        total_cost_microdollars=total_cost,
        total_requests=total_requests,
        total_users=total_users,
        total_input_tokens=total_input_tokens,
        total_output_tokens=total_output_tokens,
        avg_input_tokens_per_request=(
            avg_input_total / token_bearing_requests
            if token_bearing_requests > 0
            else 0.0
        ),
        avg_output_tokens_per_request=(
            avg_output_total / token_bearing_requests
            if token_bearing_requests > 0
            else 0.0
        ),
        avg_cost_microdollars_per_request=(
            avg_cost_total / cost_bearing_requests if cost_bearing_requests > 0 else 0.0
        ),
        cost_p50_microdollars=cost_p50,
        cost_p75_microdollars=cost_p75,
        cost_p95_microdollars=cost_p95,
        cost_p99_microdollars=cost_p99,
        cost_buckets=cost_buckets,
    )