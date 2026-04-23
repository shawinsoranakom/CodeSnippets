def check_file_based_cache_is_absolute(app_configs, **kwargs):
    errors = []
    for alias, config in settings.CACHES.items():
        cache = caches[alias]
        if not isinstance(cache, FileBasedCache):
            continue
        if not pathlib.Path(config["LOCATION"]).is_absolute():
            errors.append(
                Warning(
                    f"Your '{alias}' cache LOCATION path is relative. Use an "
                    f"absolute path instead.",
                    id="caches.W003",
                )
            )
    return errors