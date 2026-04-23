def test_module_does_not_exist(self):
        with self.assertRaisesMessage(ImportError, "No module named 'foo'"):
            get_callable("foo.bar")