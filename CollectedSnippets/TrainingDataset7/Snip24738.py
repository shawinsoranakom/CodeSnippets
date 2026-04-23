def test_get_script_name(self):
        # Regression test for #23173
        # Test first without PATH_INFO
        script_name = get_script_name({"SCRIPT_URL": "/foobar/"})
        self.assertEqual(script_name, "/foobar/")

        script_name = get_script_name({"SCRIPT_URL": "/foobar/", "PATH_INFO": "/"})
        self.assertEqual(script_name, "/foobar")