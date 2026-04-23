def main_hello(**kwargs):
    """Runs the Hello World script."""
    from streamlit.hello import Hello

    bootstrap.load_config_options(flag_options=kwargs)
    filename = Hello.__file__
    _main_run(filename, flag_options=kwargs)