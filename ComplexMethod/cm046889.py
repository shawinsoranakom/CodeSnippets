def patch_vllm_for_notebooks():
    import sys

    ipython = None
    try:
        from IPython import get_ipython as _get_ipython
    except Exception:
        _get_ipython = None

    if _get_ipython is not None:
        try:
            ipython = _get_ipython()
        except Exception:
            ipython = None

    if ipython is None:
        try:
            import builtins

            _get_ipython = getattr(builtins, "get_ipython", None)
            if callable(_get_ipython):
                ipython = _get_ipython()
        except Exception:
            ipython = None

    if ipython is None:
        return

    try:
        shell = ipython.__class__.__name__
        is_notebook = shell == "ZMQInteractiveShell" or "google.colab" in str(
            type(ipython)
        )
    except Exception:
        return

    if not is_notebook:
        return

    if not hasattr(sys.stdout, "fileno"):
        return

    needs_patch = False
    try:
        fd = sys.stdout.fileno()
        if not isinstance(fd, int) or fd < 0:
            needs_patch = True
    except Exception:
        needs_patch = True

    if not needs_patch:
        return

    logger.info(
        "Unsloth: Notebook detected - Patching sys.stdout.fileno for newer `vllm>=0.12.0` versions"
    )
    sys.stdout.fileno = lambda: 1