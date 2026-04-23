def _get_stack_trace_str_list(
    exception: BaseException, strip_streamlit_stack_entries: bool = False
) -> List[str]:
    """Get the stack trace for the given exception.

    Parameters
    ----------
    exception : BaseException
        The exception to extract the traceback from

    strip_streamlit_stack_entries : bool
        If True, all traceback entries that are in the Streamlit package
        will be removed from the list. We do this for exceptions that result
        from incorrect usage of Streamlit APIs, so that the user doesn't see
        a bunch of noise about ScriptRunner, DeltaGenerator, etc.

    Returns
    -------
    list
        The exception traceback as a list of strings

    """
    extracted_traceback: Optional[traceback.StackSummary] = None
    if isinstance(exception, StreamlitAPIWarning):
        extracted_traceback = exception.tacked_on_stack
    elif hasattr(exception, "__traceback__"):
        extracted_traceback = traceback.extract_tb(exception.__traceback__)

    if isinstance(exception, UncaughtAppException):
        extracted_traceback = traceback.extract_tb(exception.exc.__traceback__)

    # Format the extracted traceback and add it to the protobuf element.
    if extracted_traceback is None:
        stack_trace_str_list = [
            "Cannot extract the stack trace for this exception. "
            "Try calling exception() within the `catch` block."
        ]
    else:
        if strip_streamlit_stack_entries:
            extracted_frames = _get_nonstreamlit_traceback(extracted_traceback)
            stack_trace_str_list = traceback.format_list(extracted_frames)
        else:
            stack_trace_str_list = traceback.format_list(extracted_traceback)

    stack_trace_str_list = [item.strip() for item in stack_trace_str_list]

    return stack_trace_str_list