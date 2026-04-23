def config_show(**kwargs):
    """Show all of Streamlit's config settings."""

    bootstrap.load_config_options(flag_options=kwargs)

    _config.show_config()