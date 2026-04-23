def stop() -> NoReturn:
    """Stops execution immediately.

    Streamlit will not run any statements after `st.stop()`.
    We recommend rendering a message to explain why the script has stopped.
    When run outside of Streamlit, this will raise an Exception.

    Example
    -------

    >>> name = st.text_input('Name')
    >>> if not name:
    >>>   st.warning('Please input a name.')
    >>>   st.stop()
    >>> st.success('Thank you for inputting a name.')

    """
    raise StopException()