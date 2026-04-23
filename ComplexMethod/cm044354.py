def test_init(sys_info_instance: _SysInfo) -> None:
    """ Test :class:`lib.system.sysinfo._SysInfo` __init__ and attributes """
    assert isinstance(sys_info_instance, _SysInfo)

    attrs = ["_state_file", "_configs", "_system",
             "_python", "_packages", "_gpu", "_cuda", "_rocm"]
    assert all(a in sys_info_instance.__dict__ for a in attrs)
    assert all(a in attrs for a in sys_info_instance.__dict__)

    assert isinstance(sys_info_instance._state_file, str)
    assert isinstance(sys_info_instance._configs, str)
    assert isinstance(sys_info_instance._system, System)
    assert isinstance(sys_info_instance._python, dict)
    assert sys_info_instance._python == {"implementation": platform.python_implementation(),
                                         "version": platform.python_version()}
    assert isinstance(sys_info_instance._packages, Packages)
    assert isinstance(sys_info_instance._gpu, GPUInfo)
    assert isinstance(sys_info_instance._cuda, Cuda)
    assert isinstance(sys_info_instance._rocm, ROCm)