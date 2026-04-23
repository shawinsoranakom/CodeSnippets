def _check_for_nested_attribute(obj, wrong_name, attrs):
    """Check if any attribute of obj has the wrong_name as a nested attribute.

    Returns the first nested attribute suggestion found, or None.
    Limited to checking 20 attributes.
    Only considers non-descriptor outer attributes to avoid executing
    arbitrary code. Checks nested attributes statically so descriptors such
    as properties can still be suggested without invoking them.
    Skips lazy imports to avoid triggering module loading.
    """
    from inspect import getattr_static

    # Check for nested attributes (only one level deep)
    attrs_to_check = [x for x in attrs if not x.startswith('_')][:20]  # Limit number of attributes to check
    for attr_name in attrs_to_check:
        with suppress(Exception):
            # Check if attr_name is a descriptor - if so, skip it
            attr_from_class = getattr_static(type(obj), attr_name, _sentinel)
            if attr_from_class is not _sentinel and hasattr(attr_from_class, '__get__'):
                continue  # Skip descriptors to avoid executing arbitrary code

            # Skip lazy imports to avoid triggering module loading
            if _is_lazy_import(obj, attr_name):
                continue

            # Safe to get the attribute since it's not a descriptor
            attr_obj = getattr(obj, attr_name)

            if _is_lazy_import(attr_obj, wrong_name):
                continue

            if getattr_static(attr_obj, wrong_name, _sentinel) is not _sentinel:
                return f"{attr_name}.{wrong_name}"

    return None