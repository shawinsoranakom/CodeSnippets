def test_weakref_in_sys_module(self):
        """iter_all_python_module_file() ignores weakref modules."""
        time_proxy = weakref.proxy(time)
        sys.modules["time_proxy"] = time_proxy
        self.addCleanup(lambda: sys.modules.pop("time_proxy", None))
        list(autoreload.iter_all_python_module_files())