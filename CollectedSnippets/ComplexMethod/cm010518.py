def _raw_device_count_zes(visible_mask: list[int]) -> int:
    r"""Return the number of visible XPU devices via Level Zero Sysman.

    Enumerates devices from the first Level Zero Sysman driver and counts those
    whose logical index appears in *visible_mask*.  Only devices listed in
    the visible mask participate in counting.

    Discrete GPUs (dGPUs) take priority: if any visible dGPU is found, only
    dGPUs are counted; integrated GPUs (iGPUs) are counted only when no
    visible dGPU exists.

    For tiled dGPUs (``numSubdevices > 0``), the counting depends on
    ``ZE_FLAT_DEVICE_HIERARCHY``:

    - **FLAT / COMBINED** (default): each sub-device is exposed as a
      separate top-level device and counted individually.
    - **COMPOSITE**: sub-devices are hidden; the whole physical device
      counts as one.

    Returns a negative value on initialization or enumeration failure.
    """
    from ctypes import byref, c_uint32

    try:
        import pyzes  # type: ignore[import]
    except ImportError:
        return -1

    def _zes_check(rc: int, msg: str) -> bool:
        """Return True if the call failed (rc != 0) after issuing a warning."""
        if rc != 0:
            warnings.warn(msg, stacklevel=3)
        return rc != 0

    if _zes_check(pyzes.zesInit(0), "Can't initialize Level Zero Sysman"):
        return -1

    driver_count = c_uint32(0)
    if _zes_check(
        pyzes.zesDriverGet(byref(driver_count), None),
        "Can't get Level Zero Sysman driver count",
    ):
        return -1
    if driver_count.value == 0:
        return 0

    drivers = (pyzes.zes_driver_handle_t * driver_count.value)()
    if _zes_check(
        pyzes.zesDriverGet(byref(driver_count), drivers),
        "Can't get Level Zero Sysman driver handles",
    ):
        return -1

    device_count = c_uint32(0)
    if _zes_check(
        pyzes.zesDeviceGet(drivers[0], byref(device_count), None),
        "Can't get Level Zero Sysman device count",
    ):
        return -1

    devices = (pyzes.zes_device_handle_t * device_count.value)()
    if _zes_check(
        pyzes.zesDeviceGet(drivers[0], byref(device_count), devices),
        "Can't get Level Zero Sysman device handles",
    ):
        return -1

    # --- Count visible dGPUs and iGPUs ---
    ZE_DEVICE_PROPERTY_FLAG_INTEGRATED = 1 << 0
    hierarchy = os.getenv("ZE_FLAT_DEVICE_HIERARCHY")
    expose_sub_devices = hierarchy != "COMPOSITE"

    visible = set(visible_mask)
    logical_index = 0
    num_igpu = 0
    num_dgpu = 0

    for device in devices:
        props = pyzes.zes_device_properties_t()
        props.stype = pyzes.ZES_STRUCTURE_TYPE_DEVICE_PROPERTIES
        if _zes_check(
            pyzes.zesDeviceGetProperties(device, byref(props)),
            "Can't get Level Zero Sysman device properties",
        ):
            return -1

        is_integrated = bool(props.core.flags & ZE_DEVICE_PROPERTY_FLAG_INTEGRATED)

        # Determine how many logical indices this physical device occupies.
        # Tiled dGPUs in FLAT/COMBINED mode expose each sub-device separately;
        # everything else (iGPU, non-tiled dGPU, COMPOSITE mode) counts as one.
        num_slots = (
            props.numSubdevices
            if not is_integrated and props.numSubdevices > 0 and expose_sub_devices
            else 1
        )

        for _ in range(num_slots):
            if logical_index in visible:
                if is_integrated:
                    num_igpu += 1
                else:
                    num_dgpu += 1
            logical_index += 1

    # Prefer dGPU count; fall back to iGPU count only when no dGPU is visible.
    return num_dgpu or num_igpu