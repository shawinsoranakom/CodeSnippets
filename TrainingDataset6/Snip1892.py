def callback() -> None:
    # For MacOS with Cairo
    os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = "/opt/homebrew/lib"