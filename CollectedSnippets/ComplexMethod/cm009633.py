def _get_key(
    key: str,
    scopes: Scopes,
    *,
    warn: bool,
    keep: bool,
    def_ldel: str,
    def_rdel: str,
) -> Any:
    """Retrieve a value from the current scope using a dot-separated key path.

    Traverses through nested dictionaries and lists using dot notation.

    Supports special key `'.'` to return the current scope.

    Args:
        key: Dot-separated key path (e.g., `'user.name'` or `'.'` for current scope).
        scopes: List of scope dictionaries to search through.
        warn: Whether to log a warning when a key is not found.
        keep: Whether to return the original template tag when key is not found.
        def_ldel: Left delimiter for template (used when keep is `True`).
        def_rdel: Right delimiter for template (used when keep is `True`).

    Returns:
        The value found at the key path.

            If not found, returns the original template tag when keep is `True`,
            otherwise returns an empty string.
    """
    # If the key is a dot
    if key == ".":
        # Then just return the current scope
        return scopes[0]

    # Loop through the scopes
    for scope in scopes:
        try:
            # Return an empty string if falsy, with two exceptions
            # 0 should return 0, and False should return False
            if scope in (0, False):
                return scope

            resolved_scope = scope
            # For every dot separated key
            for child in key.split("."):
                # Return an empty string if falsy, with two exceptions
                # 0 should return 0, and False should return False
                if resolved_scope in (0, False):
                    return resolved_scope
                # Move into the scope
                if isinstance(resolved_scope, dict):
                    try:
                        resolved_scope = resolved_scope[child]
                    except (KeyError, TypeError):
                        # Key not found - will be caught by outer try-except
                        msg = f"Key {child!r} not found in dict"
                        raise KeyError(msg) from None
                elif isinstance(resolved_scope, (list, tuple)):
                    try:
                        resolved_scope = resolved_scope[int(child)]
                    except (ValueError, IndexError, TypeError):
                        # Invalid index - will be caught by outer try-except
                        msg = f"Invalid index {child!r} for list/tuple"
                        raise IndexError(msg) from None
                else:
                    # Reject everything else for security
                    # This prevents traversing into arbitrary Python objects
                    msg = (
                        f"Cannot traverse into {type(resolved_scope).__name__}. "
                        "Mustache templates only support dict, list, and tuple. "
                        f"Got: {type(resolved_scope)}"
                    )
                    raise TypeError(msg)  # noqa: TRY301

            try:
                # This allows for custom falsy data types
                # https://github.com/noahmorrison/chevron/issues/35
                if resolved_scope._CHEVRON_return_scope_when_falsy:  # type: ignore[union-attr] # noqa: SLF001
                    return resolved_scope
            except AttributeError:
                if resolved_scope in (0, False):
                    return resolved_scope
                return resolved_scope or ""
        except (AttributeError, KeyError, IndexError, ValueError, TypeError):
            # We couldn't find the key in the current scope
            # TypeError: Attempted to traverse into non-dict/list type
            # We'll try again on the next pass
            pass

    # We couldn't find the key in any of the scopes

    if warn:
        logger.warning("Could not find key '%s'", key)

    if keep:
        return f"{def_ldel} {key} {def_rdel}"

    return ""