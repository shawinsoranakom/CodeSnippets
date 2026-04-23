def test__gpu_stats_init_(gpu_stats_instance: _GPUStats) -> None:
    """ Test that the base :class:`~lib.gpu_stats._base._GPUStats` class initializes correctly

    Parameters
    ----------
    gpu_stats_instance: :class:`_GPUStats`
        Fixture instance of the _GPUStats base class
    """
    # Ensure that the object is initialized and shutdown correctly
    assert gpu_stats_instance._is_initialized is False
    assert T.cast(MagicMock, gpu_stats_instance._initialize).call_count == 1
    assert T.cast(MagicMock, gpu_stats_instance._shutdown).call_count == 1

    # Ensure that the object correctly gets and stores the device count, active devices,
    # handles, driver, device names, and VRAM information
    assert gpu_stats_instance.device_count == _DummyData.device_count
    assert gpu_stats_instance._active_devices == _DummyData.active_devices
    assert gpu_stats_instance._handles == _DummyData.handles
    assert gpu_stats_instance._driver == _DummyData.driver
    assert gpu_stats_instance._device_names == _DummyData.device_names
    assert gpu_stats_instance._vram == _DummyData.vram