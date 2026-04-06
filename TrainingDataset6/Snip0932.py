def usage_tracker_exists(usage_tracker):
    usage_tracker.return_value \
                 .exists.return_value = True
    return usage_tracker.return_value.exists