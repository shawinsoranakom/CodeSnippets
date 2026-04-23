def main(ctx, log_level="info"):
    """Try out a demo with:

        $ streamlit hello

    Or use the line below to run your own script:

        $ streamlit run your_script.py
    """

    if log_level:
        from streamlit.logger import get_logger

        LOGGER = get_logger(__name__)
        LOGGER.warning(
            "Setting the log level using the --log_level flag is unsupported."
            "\nUse the --logger.level flag (after your streamlit command) instead."
        )