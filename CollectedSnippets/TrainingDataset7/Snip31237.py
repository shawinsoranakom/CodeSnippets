def get_apps_to_install(test_modules):
    for test_module in test_modules:
        if test_module in CONTRIB_TESTS_TO_APPS:
            yield from CONTRIB_TESTS_TO_APPS[test_module]
        yield test_module

    # Add contrib.gis to INSTALLED_APPS if needed (rather than requiring
    # @override_settings(INSTALLED_APPS=...) on all test cases.
    if connection.features.gis_enabled:
        yield "django.contrib.gis"