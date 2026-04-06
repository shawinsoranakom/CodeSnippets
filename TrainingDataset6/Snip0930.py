def usage_tracker(mocker):
    return mocker.patch(
        'thefuck.entrypoints.not_configured._get_not_configured_usage_tracker_path',
        new_callable=MagicMock)