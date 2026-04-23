def _check_conflicts() -> None:
    # Node-related conflicts

    # When using the Node server, we must always connect to 8501 (this is
    # hard-coded in JS). Otherwise, the browser would decide what port to
    # connect to based on window.location.port, which in dev is going to
    # be (3000)

    # Import logger locally to prevent circular references
    from streamlit.logger import get_logger

    LOGGER = get_logger(__name__)

    if get_option("global.developmentMode"):
        assert _is_unset(
            "server.port"
        ), "server.port does not work when global.developmentMode is true."

        assert _is_unset("browser.serverPort"), (
            "browser.serverPort does not work when global.developmentMode is " "true."
        )

    # XSRF conflicts
    if get_option("server.enableXsrfProtection"):
        if not get_option("server.enableCORS") or get_option("global.developmentMode"):
            LOGGER.warning(
                """
Warning: the config option 'server.enableCORS=false' is not compatible with 'server.enableXsrfProtection=true'.
As a result, 'server.enableCORS' is being overridden to 'true'.

More information:
In order to protect against CSRF attacks, we send a cookie with each request.
To do so, we must specify allowable origins, which places a restriction on
cross-origin resource sharing.

If cross origin resource sharing is required, please disable server.enableXsrfProtection.
            """
            )