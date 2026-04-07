def test_urlconf_exception_is_used_as_cause(self):
        urlconf_exc = ValueError("Error")
        fake_method = mock.MagicMock(side_effect=RuntimeError())
        wrapped = autoreload.check_errors(fake_method)
        with mock.patch.object(autoreload, "_url_module_exception", urlconf_exc):
            try:
                with self.assertRaises(RuntimeError) as cm:
                    wrapped()
            finally:
                autoreload._exception = None
        self.assertIs(cm.exception.__cause__, urlconf_exc)