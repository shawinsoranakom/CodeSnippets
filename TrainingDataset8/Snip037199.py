def function_beta_warning(func, date):
    """Wrapper for functions that are no longer in beta.

    Wrapped functions will run as normal, but then proceed to show an st.warning
    saying that the beta_ version will be removed in ~3 months.

    Parameters
    ----------
    func: callable
        The `st.` function that used to be in beta.

    date: str
        A date like "2020-01-01", indicating the last day we'll guarantee
        support for the beta_ prefix.
    """

    def wrapped_func(*args, **kwargs):
        # Note: Since we use a wrapper, beta_ functions will not autocomplete
        # correctly on VSCode.
        result = func(*args, **kwargs)
        _show_beta_warning(func.__name__, date)
        return result

    # Update the wrapped func's name & docstring so st.help does the right thing
    wrapped_func.__name__ = "beta_" + func.__name__
    wrapped_func.__doc__ = func.__doc__
    return wrapped_func