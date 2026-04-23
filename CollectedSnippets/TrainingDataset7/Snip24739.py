def test_get_script_name_double_slashes(self):
        """
        WSGI squashes multiple successive slashes in PATH_INFO, get_script_name
        should take that into account when forming SCRIPT_NAME (#17133).
        """
        script_name = get_script_name(
            {
                "SCRIPT_URL": "/mst/milestones//accounts/login//help",
                "PATH_INFO": "/milestones/accounts/login/help",
            }
        )
        self.assertEqual(script_name, "/mst")