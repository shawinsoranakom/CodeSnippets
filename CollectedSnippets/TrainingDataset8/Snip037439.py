def marshall(exception_proto: ExceptionProto, exception: BaseException) -> None:
    """Marshalls an Exception.proto message.

    Parameters
    ----------
    exception_proto : Exception.proto
        The Exception protobuf to fill out

    exception : BaseException
        The exception whose data we're extracting
    """
    # If this is a StreamlitAPIException, we prune all Streamlit entries
    # from the exception's stack trace.
    is_api_exception = isinstance(exception, StreamlitAPIException)
    is_deprecation_exception = isinstance(exception, StreamlitDeprecationWarning)
    is_markdown_exception = isinstance(exception, MarkdownFormattedException)
    is_uncaught_app_exception = isinstance(exception, UncaughtAppException)

    stack_trace = (
        []
        if is_deprecation_exception
        else _get_stack_trace_str_list(
            exception, strip_streamlit_stack_entries=is_api_exception
        )
    )

    # Some exceptions (like UserHashError) have an alternate_name attribute so
    # we can pretend to the user that the exception is called something else.
    if getattr(exception, "alternate_name", None) is not None:
        exception_proto.type = getattr(exception, "alternate_name")
    else:
        exception_proto.type = type(exception).__name__

    exception_proto.stack_trace.extend(stack_trace)
    exception_proto.is_warning = isinstance(exception, Warning)

    try:
        if isinstance(exception, SyntaxError):
            # SyntaxErrors have additional fields (filename, text, lineno,
            # offset) that we can use for a nicely-formatted message telling
            # the user what to fix.
            exception_proto.message = _format_syntax_error_message(exception)
        else:
            exception_proto.message = str(exception).strip()
            exception_proto.message_is_markdown = is_markdown_exception

    except Exception as str_exception:
        # Sometimes the exception's __str__/__unicode__ method itself
        # raises an error.
        exception_proto.message = ""
        LOGGER.warning(
            """

Streamlit was unable to parse the data from an exception in the user's script.
This is usually due to a bug in the Exception object itself. Here is some info
about that Exception object, so you can report a bug to the original author:

Exception type:
  %(etype)s

Problem:
  %(str_exception)s

Traceback:
%(str_exception_tb)s

        """
            % {
                "etype": type(exception).__name__,
                "str_exception": str_exception,
                "str_exception_tb": "\n".join(_get_stack_trace_str_list(str_exception)),
            }
        )

    if is_uncaught_app_exception:
        uae = cast(UncaughtAppException, exception)
        exception_proto.message = _GENERIC_UNCAUGHT_EXCEPTION_TEXT
        type_str = str(type(uae.exc))
        exception_proto.type = type_str.replace("<class '", "").replace("'>", "")