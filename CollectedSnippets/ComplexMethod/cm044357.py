def test_system_init(system_instance: System) -> None:
    """ Test :class:`lib.system.System` __init__ and attributes """
    assert isinstance(system_instance, System)

    attrs = ["platform", "system", "machine", "release", "processor", "cpu_count",
             "python_implementation", "python_version", "python_architecture", "encoding",
             "is_conda", "is_admin", "is_virtual_env"]
    assert all(a in system_instance.__dict__ for a in attrs)
    assert all(a in attrs for a in system_instance.__dict__)

    assert system_instance.platform == platform.platform()
    assert system_instance.system == platform.system().lower()
    assert system_instance.machine == platform.machine()
    assert system_instance.release == platform.release()
    assert system_instance.processor == platform.processor()
    assert system_instance.cpu_count == os.cpu_count()
    assert system_instance.python_implementation == platform.python_implementation()
    assert system_instance.python_version == platform.python_version()
    assert system_instance.python_architecture == platform.architecture()[0]
    assert system_instance.encoding == locale.getpreferredencoding()
    assert system_instance.is_conda == ("conda" in sys.version.lower() or
                                        os.path.exists(os.path.join(sys.prefix, "conda-meta")))
    assert isinstance(system_instance.is_admin, bool)
    assert isinstance(system_instance.is_virtual_env, bool)