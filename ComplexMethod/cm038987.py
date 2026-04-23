def SummarizeEntries(entries, extra_step_types):
    """Print a summary of the passed in list of Target objects."""

    # Create a list that is in order by time stamp and has entries for the
    # beginning and ending of each build step (one time stamp may have multiple
    # entries due to multiple steps starting/stopping at exactly the same time).
    # Iterate through this list, keeping track of which tasks are running at all
    # times. At each time step calculate a running total for weighted time so
    # that when each task ends its own weighted time can easily be calculated.
    task_start_stop_times = []

    earliest = -1
    latest = 0
    total_cpu_time = 0
    for target in entries:
        if earliest < 0 or target.start < earliest:
            earliest = target.start
        if target.end > latest:
            latest = target.end
        total_cpu_time += target.Duration()
        task_start_stop_times.append((target.start, "start", target))
        task_start_stop_times.append((target.end, "stop", target))
    length = latest - earliest
    weighted_total = 0.0

    # Sort by the time/type records and ignore |target|
    task_start_stop_times.sort(key=lambda times: times[:2])
    # Now we have all task start/stop times sorted by when they happen. If a
    # task starts and stops on the same time stamp then the start will come
    # first because of the alphabet, which is important for making this work
    # correctly.
    # Track the tasks which are currently running.
    running_tasks = {}
    # Record the time we have processed up to so we know how to calculate time
    # deltas.
    last_time = task_start_stop_times[0][0]
    # Track the accumulated weighted time so that it can efficiently be added
    # to individual tasks.
    last_weighted_time = 0.0
    # Scan all start/stop events.
    for event in task_start_stop_times:
        time, action_name, target = event
        # Accumulate weighted time up to now.
        num_running = len(running_tasks)
        if num_running > 0:
            # Update the total weighted time up to this moment.
            last_weighted_time += (time - last_time) / float(num_running)
        if action_name == "start":
            # Record the total weighted task time when this task starts.
            running_tasks[target] = last_weighted_time
        if action_name == "stop":
            # Record the change in the total weighted task time while this task
            # ran.
            weighted_duration = last_weighted_time - running_tasks[target]
            target.SetWeightedDuration(weighted_duration)
            weighted_total += weighted_duration
            del running_tasks[target]
        last_time = time
    assert len(running_tasks) == 0

    # Warn if the sum of weighted times is off by more than half a second.
    if abs(length - weighted_total) > 500:
        print(
            "Warning: Possible corrupt ninja log, results may be "
            "untrustworthy. Length = {:.3f}, weighted total = {:.3f}".format(
                length, weighted_total
            )
        )

    entries_by_ext = defaultdict(list)
    for target in entries:
        extension = GetExtension(target, extra_step_types)
        entries_by_ext[extension].append(target)

    for key, values in entries_by_ext.items():
        print("    Longest build steps for {}:".format(key))
        values.sort(key=lambda x: x.WeightedDuration())
        for target in values[-long_count:]:
            print(
                "      {:8.1f} weighted s to build {} ({:.1f} s elapsed time)".format(
                    target.WeightedDuration(),
                    target.DescribeTargets(),
                    target.Duration(),
                )
            )

    print(
        "    {:.1f} s weighted time ({:.1f} s elapsed time sum, {:1.1f}x "
        "parallelism)".format(length, total_cpu_time, total_cpu_time * 1.0 / length)
    )
    print(
        "    {} build steps completed, average of {:1.2f}/s".format(
            len(entries), len(entries) / (length)
        )
    )