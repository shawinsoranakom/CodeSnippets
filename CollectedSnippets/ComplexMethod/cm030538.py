def dyld_default_search(name, env=None):
    yield name

    framework = framework_info(name)

    if framework is not None:
        fallback_framework_path = dyld_fallback_framework_path(env)
        for path in fallback_framework_path:
            yield os.path.join(path, framework['name'])

    fallback_library_path = dyld_fallback_library_path(env)
    for path in fallback_library_path:
        yield os.path.join(path, os.path.basename(name))

    if framework is not None and not fallback_framework_path:
        for path in DEFAULT_FRAMEWORK_FALLBACK:
            yield os.path.join(path, framework['name'])

    if not fallback_library_path:
        for path in DEFAULT_LIBRARY_FALLBACK:
            yield os.path.join(path, os.path.basename(name))