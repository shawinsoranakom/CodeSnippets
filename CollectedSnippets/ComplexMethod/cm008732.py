def initialize_pot_director(ie):
    assert ie._downloader is not None, 'Downloader not set'

    enable_trace = ie._configuration_arg(
        'pot_trace', ['false'], ie_key='youtube', casesense=False)[0] == 'true'

    if enable_trace:
        log_level = IEContentProviderLogger.LogLevel.TRACE
    elif ie.get_param('verbose', False):
        log_level = IEContentProviderLogger.LogLevel.DEBUG
    else:
        log_level = IEContentProviderLogger.LogLevel.INFO

    def get_provider_logger_and_settings(provider, logger_key):
        logger_prefix = f'{logger_key}:{provider.PROVIDER_NAME}'
        extractor_key = f'{EXTRACTOR_ARG_PREFIX}-{provider.PROVIDER_KEY.lower()}'
        return (
            YoutubeIEContentProviderLogger(ie, logger_prefix, log_level=log_level),
            ie.get_param('extractor_args', {}).get(extractor_key, {}))

    cache_providers = []
    for cache_provider in _pot_cache_providers.value.values():
        logger, settings = get_provider_logger_and_settings(cache_provider, 'pot:cache')
        cache_providers.append(cache_provider(ie, logger, settings))
    cache_spec_providers = []
    for cache_spec_provider in _pot_pcs_providers.value.values():
        logger, settings = get_provider_logger_and_settings(cache_spec_provider, 'pot:cache:spec')
        cache_spec_providers.append(cache_spec_provider(ie, logger, settings))

    cache = PoTokenCache(
        logger=YoutubeIEContentProviderLogger(ie, 'pot:cache', log_level=log_level),
        cache_providers=cache_providers,
        cache_spec_providers=cache_spec_providers,
        cache_provider_preferences=list(_pot_cache_provider_preferences.value),
    )

    director = PoTokenRequestDirector(
        logger=YoutubeIEContentProviderLogger(ie, 'pot', log_level=log_level),
        cache=cache,
    )

    ie._downloader.add_close_hook(director.close)

    for provider in _pot_providers.value.values():
        logger, settings = get_provider_logger_and_settings(provider, 'pot')
        director.register_provider(provider(ie, logger, settings))

    for preference in _ptp_preferences.value:
        director.register_preference(preference)

    if director.logger.log_level <= director.logger.LogLevel.DEBUG:
        # calling is_available() for every PO Token provider upfront may have some overhead
        director.logger.debug(f'PO Token Providers: {provider_display_list(director.providers.values())}')
        director.logger.debug(f'PO Token Cache Providers: {provider_display_list(cache.cache_providers.values())}')
        director.logger.debug(f'PO Token Cache Spec Providers: {provider_display_list(cache.cache_spec_providers.values())}')
        director.logger.trace(f'Registered {len(director.preferences)} provider preferences')
        director.logger.trace(f'Registered {len(cache.cache_provider_preferences)} cache provider preferences')

    return director