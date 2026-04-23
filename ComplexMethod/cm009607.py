def warn_deprecated(
    since: str,
    *,
    message: str = "",
    name: str = "",
    alternative: str = "",
    alternative_import: str = "",
    pending: bool = False,
    obj_type: str = "",
    addendum: str = "",
    removal: str = "",
    package: str = "",
) -> None:
    """Display a standardized deprecation.

    Args:
        since: The release at which this API became deprecated.
        message: Override the default deprecation message.

            The `%(since)s`, `%(name)s`, `%(alternative)s`, `%(obj_type)s`,
            `%(addendum)s`, and `%(removal)s` format specifiers will be replaced by the
            values of the respective arguments passed to this function.
        name: The name of the deprecated object.
        alternative: An alternative API that the user may use in place of the
            deprecated API.

            The deprecation warning will tell the user about this alternative if
            provided.
        alternative_import: An alternative import that the user may use instead.
        pending: If `True`, uses a `PendingDeprecationWarning` instead of a
            `DeprecationWarning`.

            Cannot be used together with removal.
        obj_type: The object type being deprecated.
        addendum: Additional text appended directly to the final message.
        removal: The expected removal version.

            With the default (an empty string), a removal version is automatically
            computed from since. Set to other Falsy values to not schedule a removal
            date.

            Cannot be used together with pending.
        package: The package of the deprecated object.
    """
    if not pending:
        if not removal:
            removal = f"in {removal}" if removal else "within ?? minor releases"
            msg = (
                f"Need to determine which default deprecation schedule to use. "
                f"{removal}"
            )
            raise NotImplementedError(msg)
        removal = f"in {removal}"

    if not message:
        message = ""
        package_ = (
            package or name.split(".", maxsplit=1)[0].replace("_", "-")
            if "." in name
            else "LangChain"
        )

        if obj_type:
            message += f"The {obj_type} `{name}`"
        else:
            message += f"`{name}`"

        if pending:
            message += " will be deprecated in a future version"
        else:
            message += f" was deprecated in {package_} {since}"

            if removal:
                message += f" and will be removed {removal}"

        if alternative_import:
            alt_package = alternative_import.split(".", maxsplit=1)[0].replace("_", "-")
            if alt_package == package_:
                message += f". Use {alternative_import} instead."
            else:
                alt_module, alt_name = alternative_import.rsplit(".", 1)
                message += (
                    f". An updated version of the {obj_type} exists in the "
                    f"{alt_package} package and should be used instead. To use it run "
                    f"`pip install -U {alt_package}` and import as "
                    f"`from {alt_module} import {alt_name}`."
                )
        elif alternative:
            message += f". Use {alternative} instead."

        if addendum:
            message += f" {addendum}"

    warning_cls = (
        LangChainPendingDeprecationWarning if pending else LangChainDeprecationWarning
    )
    warning = warning_cls(message)
    warnings.warn(warning, category=LangChainDeprecationWarning, stacklevel=4)