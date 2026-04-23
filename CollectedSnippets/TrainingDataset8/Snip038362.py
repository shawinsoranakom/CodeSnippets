def _fix_matplotlib_crash() -> None:
    """Set Matplotlib backend to avoid a crash.

    The default Matplotlib backend crashes Python on OSX when run on a thread
    that's not the main thread, so here we set a safer backend as a fix.
    Users can always disable this behavior by setting the config
    runner.fixMatplotlib = false.

    This fix is OS-independent. We didn't see a good reason to make this
    Mac-only. Consistency within Streamlit seemed more important.
    """
    if config.get_option("runner.fixMatplotlib"):
        try:
            # TODO: a better option may be to set
            #  os.environ["MPLBACKEND"] = "Agg". We'd need to do this towards
            #  the top of __init__.py, before importing anything that imports
            #  pandas (which imports matplotlib). Alternately, we could set
            #  this environment variable in a new entrypoint defined in
            #  setup.py. Both of these introduce additional trickiness: they
            #  need to run without consulting streamlit.config.get_option,
            #  because this would import streamlit, and therefore matplotlib.
            import matplotlib

            matplotlib.use("Agg")
        except ImportError:
            # Matplotlib is not installed. No need to do anything.
            pass