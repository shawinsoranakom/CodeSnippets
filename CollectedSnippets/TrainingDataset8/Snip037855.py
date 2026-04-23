def check_credentials():
    """Check credentials and potentially activate.

    Note
    ----
    If there is no credential file and we are in headless mode, we should not
    check, since credential would be automatically set to an empty string.

    """
    from streamlit import config

    if not _check_credential_file_exists() and config.get_option("server.headless"):
        if not config.is_manually_set("browser.gatherUsageStats"):
            # If not manually defined, show short message about usage stats gathering.
            click.secho(_TELEMETRY_HEADLESS_TEXT)
        return
    Credentials.get_current()._check_activated()