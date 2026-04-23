def _array_api_for_tests(array_namespace, device_name=None):
    """Return (xp, device) for array API testing.

    Parameters
    ----------
    array_namespace : str
        The importable name of the array namespace module.
    device_name : str or None, default=None
        The device name for array allocation. Can be None for default device.

    Returns
    -------
    xp : module
        The module object for the requested array namespace.
    device : object, str or None
        The library specific device object that can be passed to
        xp.asarray(..., device=device). This might be a string and not
        a library specific device object.
    """
    try:
        array_mod = importlib.import_module(array_namespace)
    except (ModuleNotFoundError, ImportError):
        raise SkipTest(
            f"{array_namespace} is not installed: not checking array_api input"
        )

    if os.environ.get("SCIPY_ARRAY_API") is None:
        raise SkipTest("SCIPY_ARRAY_API is not set: not checking array_api input")

    from sklearn.externals.array_api_compat import get_namespace

    # First create an array using the chosen array module and then get the
    # corresponding (compatibility wrapped) array namespace based on it.
    # This is because `cupy` is not the same as the compatibility wrapped
    # namespace of a CuPy array.
    device = None
    xp = get_namespace(array_mod.asarray(1))
    if (
        array_namespace == "torch"
        and device_name == "cuda"
        and not xp.backends.cuda.is_built()
    ):
        raise SkipTest("PyTorch test requires cuda, which is not available")
    elif array_namespace == "torch" and device_name == "mps":
        if os.getenv("PYTORCH_ENABLE_MPS_FALLBACK") != "1":
            # For now we need PYTORCH_ENABLE_MPS_FALLBACK=1 for all estimators to work
            # when using the MPS device.
            raise SkipTest(
                "Skipping MPS device test because PYTORCH_ENABLE_MPS_FALLBACK is not "
                "set."
            )
        if not xp.backends.mps.is_built():
            raise SkipTest(
                "MPS is not available because the current PyTorch install was not "
                "built with MPS enabled."
            )
    elif array_namespace == "torch" and device_name == "xpu":  # pragma: nocover
        if not hasattr(xp, "xpu"):
            # skip xpu testing for PyTorch <2.4
            raise SkipTest(
                "XPU is not available because the current PyTorch install was not "
                "built with XPU support."
            )
        if not xp.xpu.is_available():
            raise SkipTest(
                "Skipping XPU device test because no XPU device is available"
            )
    elif array_namespace == "cupy":  # pragma: nocover
        import cupy

        if cupy.cuda.runtime.getDeviceCount() == 0:
            raise SkipTest("CuPy test requires cuda, which is not available")
    elif array_namespace == "array_api_strict":
        # device_name can be a string ("CPU_DEVICE", "device1") or a Device object
        # from yield_mixed_namespace_input_permutations
        if device_name is not None:
            device = xp.Device(device_name)

    # Right now only array_api_strict uses a library specific device
    # object. For all other libraries we return a string or `None`.
    # This works because strings are accepted as arguments to
    # xp.asarray(..., device=) in those libraries.
    return xp, device_name if device is None else device