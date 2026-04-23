def _sycl_compiler() -> str:
    # Search order:
    # 0) which icpx
    # 1) config.xpu.oneapi_root
    # 2) ONEAPI_ROOT environment variable
    # 3) default system search PATH.
    if shutil.which("icpx"):
        return "icpx"

    if os.path.exists(config.xpu.oneapi_root or ""):
        oneapi_root = config.xpu.oneapi_root
    elif os.path.exists(os.getenv("ONEAPI_ROOT") or ""):
        oneapi_root = os.getenv("ONEAPI_ROOT")
    else:
        oneapi_root = None

    if oneapi_root:
        oneapi_inclue = os.path.join(oneapi_root, "include")
        if "CPLUS_INCLUDE_PATH" in os.environ:
            os.environ["CPLUS_INCLUDE_PATH"] += ":" + oneapi_inclue
        else:
            os.environ["CPLUS_INCLUDE_PATH"] = oneapi_inclue
        return os.path.realpath(os.path.join(oneapi_root, "bin/icpx"))
    else:
        raise RuntimeError("Can not find Intel compiler.")