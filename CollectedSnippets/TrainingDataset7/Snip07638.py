def uninstall_if_needed(setting, value, enter, **kwargs):
    """
    Undo the effects of PostgresConfig.ready() when django.contrib.postgres
    is "uninstalled" by override_settings().
    """
    if (
        not enter
        and setting == "INSTALLED_APPS"
        and "django.contrib.postgres" not in set(value)
    ):
        connection_created.disconnect(register_type_handlers)
        CharField._unregister_lookup(Unaccent)
        TextField._unregister_lookup(Unaccent)
        CharField._unregister_lookup(SearchLookup)
        TextField._unregister_lookup(SearchLookup)
        CharField._unregister_lookup(TrigramSimilar)
        TextField._unregister_lookup(TrigramSimilar)
        CharField._unregister_lookup(TrigramWordSimilar)
        TextField._unregister_lookup(TrigramWordSimilar)
        CharField._unregister_lookup(TrigramStrictWordSimilar)
        TextField._unregister_lookup(TrigramStrictWordSimilar)
        # Disconnect this receiver until the next time this app is installed
        # and ready() connects it again to prevent unnecessary processing on
        # each setting change.
        setting_changed.disconnect(uninstall_if_needed)
        MigrationWriter.unregister_serializer(RANGE_TYPES)