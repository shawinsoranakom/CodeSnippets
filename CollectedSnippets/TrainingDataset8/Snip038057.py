def _clean_problem_modules() -> None:
    """Some modules are stateful, so we have to clear their state."""

    if "keras" in sys.modules:
        try:
            keras = sys.modules["keras"]
            keras.backend.clear_session()
        except Exception:
            # We don't want to crash the app if we can't clear the Keras session.
            pass

    if "matplotlib.pyplot" in sys.modules:
        try:
            plt = sys.modules["matplotlib.pyplot"]
            plt.close("all")
        except Exception:
            # We don't want to crash the app if we can't close matplotlib
            pass