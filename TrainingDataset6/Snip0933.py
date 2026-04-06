def _assert_tracker_updated(usage_tracker_io, pid):
    usage_tracker_io.seek(0)
    info = json.load(usage_tracker_io)
    assert info['pid'] == pid