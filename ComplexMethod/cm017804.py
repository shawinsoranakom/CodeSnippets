def forbid_multi_line_headers(name, val, encoding):
    """Forbid multi-line headers to prevent header injection."""
    warnings.warn(
        "The internal API forbid_multi_line_headers() is deprecated."
        " Python's modern email API (with email.message.EmailMessage or"
        " email.policy.default) will reject multi-line headers.",
        RemovedInDjango70Warning,
    )

    encoding = encoding or settings.DEFAULT_CHARSET
    val = str(val)  # val may be lazy
    if "\n" in val or "\r" in val:
        raise BadHeaderError(
            "Header values can't contain newlines (got %r for header %r)" % (val, name)
        )
    try:
        val.encode("ascii")
    except UnicodeEncodeError:
        if name.lower() in ADDRESS_HEADERS:
            val = ", ".join(
                sanitize_address(addr, encoding) for addr in getaddresses((val,))
            )
        else:
            val = Header(val, encoding).encode()
    else:
        if name.lower() == "subject":
            val = Header(val).encode()
    return name, val