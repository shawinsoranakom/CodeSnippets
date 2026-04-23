def test_full_info(sys_info_instance: _SysInfo) -> None:
    """ Test the full_info method of :class:`lib.system.sysinfo._SysInfo` returns as expected """
    assert hasattr(sys_info_instance, "full_info")
    sys_info = sys_info_instance.full_info()
    assert isinstance(sys_info, str)

    sections = ["System Information", "Pip Packages", "Configs"]
    for section in sections:
        assert section in sys_info, f"Section {section} not in full_info"
    if sys_info_instance._system.is_conda:
        assert "Conda Packages" in sys_info
    else:
        assert "Conda Packages" not in sys_info

    keys = ["backend", "os_platform", "os_machine", "os_release", "py_conda_version",
            "py_implementation", "py_version", "py_command", "py_virtual_env", "sys_cores",
            "sys_processor", "sys_ram", "encoding", "git_branch", "git_commits",
            "gpu_cuda_versions", "gpu_cuda", "gpu_cudnn", "gpu_rocm_versions", "gpu_rocm_version",
            "gpu_driver", "gpu_devices", "gpu_vram", "gpu_devices_active"]
    for key in keys:
        assert f"{key}:" in sys_info, f"'{key}:' not in full_info"