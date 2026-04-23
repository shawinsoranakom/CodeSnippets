def _convert_deprecations(value: object) -> list[_messages.DeprecationSummary] | None:
    if not value:
        return None

    if not isinstance(value, list):
        display.warning(f"Task result `deprecations` was {native_type_name(value)} instead of {native_type_name(list)} and has been discarded.")
        return None

    deprecations: list[_messages.DeprecationSummary] = []

    for deprecation in value:
        if not isinstance(deprecation, _messages.DeprecationSummary):
            # translate non-DeprecationSummary message dicts
            try:
                if (collection_name := deprecation.pop('collection_name', ...)) is not ...:
                    # deprecated: description='enable the deprecation message for collection_name' core_version='2.23'
                    # CAUTION: This deprecation cannot be enabled until the replacement (deprecator) has been documented, and the schema finalized.
                    # self.deprecated('The `collection_name` key in the `deprecations` dictionary is deprecated.', version='2.27')
                    deprecation.update(deprecator=deprecator_from_collection_name(collection_name))

                deprecation = _messages.DeprecationSummary(
                    event=_messages.Event(
                        msg=deprecation.pop('msg'),
                    ),
                    **deprecation,
                )
            except Exception as ex:
                display.error_as_warning("Task result `deprecations` contained an invalid item.", exception=ex)

        if warning_ctx := _display_utils.DeferredWarningContext.current(optional=True):
            warning_ctx.capture(deprecation)
        else:
            deprecations.append(deprecation)

    return deprecations