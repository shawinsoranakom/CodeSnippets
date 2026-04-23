async def get_orphaned_schedules_details() -> List[OrphanedScheduleDetail]:
    """
    Get detailed list of orphaned schedules with orphan reasons.

    Returns:
        List of OrphanedScheduleDetail objects
    """
    scheduler = get_scheduler_client()

    # Get all schedules
    all_schedules = await scheduler.get_execution_schedules()
    user_schedules = [s for s in all_schedules if s.id not in SYSTEM_JOB_IDS]

    # Detect orphans with categorization
    orphan_categories = await _detect_orphaned_schedules(user_schedules)

    # Build detailed orphan list
    results = []
    for orphan_type, schedule_ids in orphan_categories.items():
        for schedule_id in schedule_ids:
            # Find the schedule
            schedule = next((s for s in user_schedules if s.id == schedule_id), None)
            if not schedule:
                continue

            results.append(
                OrphanedScheduleDetail(
                    schedule_id=schedule.id,
                    schedule_name=schedule.name,
                    graph_id=schedule.graph_id,
                    graph_version=schedule.graph_version,
                    user_id=schedule.user_id,
                    orphan_reason=orphan_type,
                    error_detail=None,  # Could add more detail in future
                    next_run_time=schedule.next_run_time,
                )
            )

    return results