def _setup_environment(environ):
    # Cygwin requires some special voodoo to set the environment variables
    # properly so that Oracle will see them.
    if platform.system().upper().startswith("CYGWIN"):
        try:
            import ctypes
        except ImportError as e:
            raise ImproperlyConfigured(
                "Error loading ctypes: %s; "
                "the Oracle backend requires ctypes to "
                "operate correctly under Cygwin." % e
            )
        kernel32 = ctypes.CDLL("kernel32")
        for name, value in environ:
            kernel32.SetEnvironmentVariableA(name, value)
    else:
        os.environ.update(environ)