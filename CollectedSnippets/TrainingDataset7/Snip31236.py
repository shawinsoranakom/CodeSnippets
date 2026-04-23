def get_installed():
    return [app_config.name for app_config in apps.get_app_configs()]