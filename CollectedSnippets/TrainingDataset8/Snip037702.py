def _populate_config_msg(msg: Config) -> None:
    msg.gather_usage_stats = config.get_option("browser.gatherUsageStats")
    msg.max_cached_message_age = config.get_option("global.maxCachedMessageAge")
    msg.mapbox_token = config.get_option("mapbox.token")
    msg.allow_run_on_save = config.get_option("server.allowRunOnSave")
    msg.hide_top_bar = config.get_option("ui.hideTopBar")
    msg.hide_sidebar_nav = config.get_option("ui.hideSidebarNav")