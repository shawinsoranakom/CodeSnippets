def test_xdev(self):
        # sys.flags.dev_mode
        code = "import sys; print(sys.flags.dev_mode)"
        out = self.run_xdev("-c", code, xdev=False)
        self.assertEqual(out, "False")
        out = self.run_xdev("-c", code)
        self.assertEqual(out, "True")

        # Warnings
        code = ("import warnings; "
                "print(' '.join('%s::%s' % (f[0], f[2].__name__) "
                                "for f in warnings.filters))")
        if support.Py_DEBUG:
            expected_filters = "default::Warning"
        else:
            expected_filters = ("default::Warning "
                                "default::DeprecationWarning "
                                "ignore::DeprecationWarning "
                                "ignore::PendingDeprecationWarning "
                                "ignore::ImportWarning "
                                "ignore::ResourceWarning")

        out = self.run_xdev("-c", code)
        self.assertEqual(out, expected_filters)

        out = self.run_xdev("-b", "-c", code)
        self.assertEqual(out, f"default::BytesWarning {expected_filters}")

        out = self.run_xdev("-bb", "-c", code)
        self.assertEqual(out, f"error::BytesWarning {expected_filters}")

        out = self.run_xdev("-Werror", "-c", code)
        self.assertEqual(out, f"error::Warning {expected_filters}")

        # Memory allocator debug hooks
        try:
            import _testinternalcapi  # noqa: F401
        except ImportError:
            pass
        else:
            code = "import _testinternalcapi; print(_testinternalcapi.pymem_getallocatorsname())"
            with support.SuppressCrashReport():
                out = self.run_xdev("-c", code, check_exitcode=False)
            if support.with_pymalloc():
                alloc_name = "pymalloc_debug"
            elif support.Py_GIL_DISABLED:
                alloc_name = "mimalloc_debug"
            else:
                alloc_name = "malloc_debug"
            self.assertEqual(out, alloc_name)

        # Faulthandler
        try:
            import faulthandler  # noqa: F401
        except ImportError:
            pass
        else:
            code = "import faulthandler; print(faulthandler.is_enabled())"
            out = self.run_xdev("-c", code)
            self.assertEqual(out, "True")