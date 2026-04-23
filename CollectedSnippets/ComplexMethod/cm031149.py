def _bootstrap(*, root=None, upgrade=False, user=False,
              altinstall=False, default_pip=False,
              verbosity=0):
    """
    Bootstrap pip into the current Python installation (or the given root
    directory). Returns pip command status code.

    Note that calling this function will alter both sys.path and os.environ.
    """

    try:
        import zlib
    except ImportError:
        raise ModuleNotFoundError(
            "ensurepip requires the standard library module 'zlib' "
            "to install pip."
        ) from None

    if altinstall and default_pip:
        raise ValueError("Cannot use altinstall and default_pip together")

    sys.audit("ensurepip.bootstrap", root)

    _disable_pip_configuration_settings()

    # By default, installing pip installs all of the
    # following scripts (X.Y == running Python version):
    #
    #   pip, pipX, pipX.Y
    #
    # pip 1.5+ allows ensurepip to request that some of those be left out
    if altinstall:
        # omit pip, pipX
        os.environ["ENSUREPIP_OPTIONS"] = "altinstall"
    elif not default_pip:
        # omit pip
        os.environ["ENSUREPIP_OPTIONS"] = "install"

    with tempfile.TemporaryDirectory() as tmpdir:
        # Put our bundled wheels into a temporary directory and construct the
        # additional paths that need added to sys.path
        tmpdir_path = Path(tmpdir)
        with _get_pip_whl_path_ctx() as bundled_wheel_path:
            tmp_wheel_path = tmpdir_path / bundled_wheel_path.name
            copy2(bundled_wheel_path, tmp_wheel_path)

        # Construct the arguments to be passed to the pip command
        args = ["install", "--no-cache-dir", "--no-index", "--find-links", tmpdir]
        if root:
            args += ["--root", root]
        if upgrade:
            args += ["--upgrade"]
        if user:
            args += ["--user"]
        if verbosity:
            args += ["-" + "v" * verbosity]
        if sys.implementation.cache_tag is None:
            args += ["--no-compile"]

        return _run_pip([*args, "pip"], [os.fsdecode(tmp_wheel_path)])