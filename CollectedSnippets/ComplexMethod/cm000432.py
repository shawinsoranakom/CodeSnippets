async def get_schedule_health_metrics() -> ScheduleHealthMetrics:
    """
    Get comprehensive schedule diagnostics via Scheduler service.

    Returns:
        ScheduleHealthMetrics with schedule health info
    """
    scheduler = get_scheduler_client()

    # Get all schedules from scheduler service
    all_schedules = await scheduler.get_execution_schedules()

    # Filter user vs system schedules
    user_schedules = [s for s in all_schedules if s.id not in SYSTEM_JOB_IDS]
    system_schedules_count = len(all_schedules) - len(user_schedules)

    # Detect orphaned schedules
    orphans = await _detect_orphaned_schedules(user_schedules)

    # Count schedules by next run time (exclude orphaned schedules)
    now = datetime.now(timezone.utc)
    one_hour_from_now = now + timedelta(hours=1)
    twenty_four_hours_from_now = now + timedelta(hours=24)

    orphaned_ids = set()
    for category_ids in orphans.values():
        orphaned_ids.update(category_ids)

    healthy_schedules = [s for s in user_schedules if s.id not in orphaned_ids]

    schedules_next_hour = sum(
        1
        for s in healthy_schedules
        if s.next_run_time
        and datetime.fromisoformat(s.next_run_time.replace("Z", "+00:00"))
        <= one_hour_from_now
    )

    schedules_next_24h = sum(
        1
        for s in healthy_schedules
        if s.next_run_time
        and datetime.fromisoformat(s.next_run_time.replace("Z", "+00:00"))
        <= twenty_four_hours_from_now
    )

    # Calculate total execution runs (not just unique schedules, exclude orphaned)
    total_runs_next_hour = _calculate_total_runs(
        healthy_schedules, now, one_hour_from_now
    )
    total_runs_next_24h = _calculate_total_runs(
        healthy_schedules, now, twenty_four_hours_from_now
    )

    return ScheduleHealthMetrics(
        total_schedules=len(all_schedules),
        user_schedules=len(user_schedules),
        system_schedules=system_schedules_count,
        orphaned_deleted_graph=len(orphans["deleted_graph"]),
        orphaned_no_library_access=len(orphans["no_library_access"]),
        orphaned_invalid_credentials=len(orphans["invalid_credentials"]),
        orphaned_validation_failed=len(orphans["validation_failed"]),
        total_orphaned=sum(len(v) for v in orphans.values()),
        schedules_next_hour=schedules_next_hour,
        schedules_next_24h=schedules_next_24h,
        total_runs_next_hour=total_runs_next_hour,
        total_runs_next_24h=total_runs_next_24h,
        timestamp=now.isoformat(),
    )