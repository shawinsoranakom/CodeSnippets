def ReadTargets(log, show_all):
    """Reads all targets from .ninja_log file |log_file|, sorted by duration.

    The result is a list of Target objects."""
    header = log.readline()
    assert header == "# ninja log v5\n", "unrecognized ninja log version {!r}".format(
        header
    )
    targets_dict = {}
    last_end_seen = 0.0
    for line in log:
        parts = line.strip().split("\t")
        if len(parts) != 5:
            # If ninja.exe is rudely halted then the .ninja_log file may be
            # corrupt. Silently continue.
            continue
        start, end, _, name, cmdhash = parts  # Ignore restart.
        # Convert from integral milliseconds to float seconds.
        start = int(start) / 1000.0
        end = int(end) / 1000.0
        if not show_all and end < last_end_seen:
            # An earlier time stamp means that this step is the first in a new
            # build, possibly an incremental build. Throw away the previous
            # data so that this new build will be displayed independently.
            # This has to be done by comparing end times because records are
            # written to the .ninja_log file when commands complete, so end
            # times are guaranteed to be in order, but start times are not.
            targets_dict = {}
        target = None
        if cmdhash in targets_dict:
            target = targets_dict[cmdhash]
            if not show_all and (target.start != start or target.end != end):
                # If several builds in a row just run one or two build steps
                # then the end times may not go backwards so the last build may
                # not be detected as such. However in many cases there will be a
                # build step repeated in the two builds and the changed
                # start/stop points for that command, identified by the hash,
                # can be used to detect and reset the target dictionary.
                targets_dict = {}
                target = None
        if not target:
            targets_dict[cmdhash] = target = Target(start, end)
        last_end_seen = end
        target.targets.append(name)
    return list(targets_dict.values())