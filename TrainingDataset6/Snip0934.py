def _change_tracker(usage_tracker_io, pid):
    usage_tracker_io.truncate(0)
    info = {'pid': pid, 'time': 0}
    json.dump(info, usage_tracker_io)
    usage_tracker_io.seek(0)