def spinner(text: str = "In progress...") -> Iterator[None]:
    """Temporarily displays a message while executing a block of code.

    Parameters
    ----------
    text : str
        A message to display while executing that block

    Example
    -------

    >>> with st.spinner('Wait for it...'):
    >>>     time.sleep(5)
    >>> st.success('Done!')

    """
    import streamlit.runtime.caching as caching
    import streamlit.runtime.legacy_caching.caching as legacy_caching
    from streamlit.proto.Spinner_pb2 import Spinner as SpinnerProto
    from streamlit.string_util import clean_text

    # @st.cache optionally uses spinner for long-running computations.
    # Normally, streamlit warns the user when they call st functions
    # from within an @st.cache'd function. But we do *not* want to show
    # these warnings for spinner's message, so we create and mutate this
    # message delta within the "suppress_cached_st_function_warning"
    # context.
    with legacy_caching.suppress_cached_st_function_warning():
        with caching.suppress_cached_st_function_warning():
            message = st.empty()

    # Set the message 0.1 seconds in the future to avoid annoying
    # flickering if this spinner runs too quickly.
    DELAY_SECS = 0.1
    display_message = True
    display_message_lock = threading.Lock()

    try:

        def set_message():
            with display_message_lock:
                if display_message:
                    with legacy_caching.suppress_cached_st_function_warning():
                        with caching.suppress_cached_st_function_warning():
                            spinner_proto = SpinnerProto()
                            spinner_proto.text = clean_text(text)
                            message._enqueue("spinner", spinner_proto)

        add_script_run_ctx(threading.Timer(DELAY_SECS, set_message)).start()

        # Yield control back to the context.
        yield
    finally:
        if display_message_lock:
            with display_message_lock:
                display_message = False
        with legacy_caching.suppress_cached_st_function_warning():
            with caching.suppress_cached_st_function_warning():
                message.empty()