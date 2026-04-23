def _record_overlap_intervals(intervals):
    boundaries = sorted(_boundaries(intervals, 'start', 'stop'))
    counts = {}
    interval_vals = []
    ids = set()
    start = None
    for (time, flag, records) in boundaries:
        for record in records:
            if (
                new_count := counts.get(record.id, 0) + {'start': 1, 'stop': -1}[flag]
            ):
                counts[record.id] = new_count
            else:
                del counts[record.id]
        new_ids = set(counts.keys())
        if ids != new_ids:
            if ids and start is not None:
                interval_vals.append((start, time, records.browse(ids)))
            if new_ids:
                start = time
        ids = new_ids
    return Intervals(interval_vals, keep_distinct=True)