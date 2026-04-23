def register_converter(converter, type_name):
    if type_name in REGISTERED_CONVERTERS or type_name in DEFAULT_CONVERTERS:
        raise ValueError(f"Converter {type_name!r} is already registered.")
    REGISTERED_CONVERTERS[type_name] = converter()
    get_converters.cache_clear()

    from django.urls.resolvers import _route_to_regex

    _route_to_regex.cache_clear()