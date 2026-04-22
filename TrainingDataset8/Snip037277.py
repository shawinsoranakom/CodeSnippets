def _maybe_read_env_variable(value: Any) -> Any:
    """If value is "env:foo", return value of environment variable "foo".

    If value is not in the shape above, returns the value right back.

    Parameters
    ----------
    value : any
        The value to check

    Returns
    -------
    any
        Either returns value right back, or the value of the environment
        variable.

    """

    if isinstance(value, str) and value.startswith("env:"):
        var_name = value[len("env:") :]
        env_var = os.environ.get(var_name)

        if env_var is None:
            # Import logger locally to prevent circular references
            from streamlit.logger import get_logger

            LOGGER = get_logger(__name__)

            LOGGER.error("No environment variable called %s" % var_name)
        else:
            return _maybe_convert_to_number(env_var)

    return value