def test_client_driver_info(self):
        client_info = cache._cache.get_client().client_info()
        if {"lib-name", "lib-ver"}.issubset(client_info):
            version = django.get_version()
            if hasattr(self.lib, "DriverInfo"):
                info = self.lib.DriverInfo().add_upstream_driver("django", version)
                correct_lib_name = info.formatted_name
            else:
                correct_lib_name = f"redis-py(django_v{version})"
            # Relax the assertion to allow date variance in editable installs.
            truncated_lib_name = correct_lib_name.rsplit(".dev", maxsplit=1)[0]
            self.assertIn(truncated_lib_name, client_info["lib-name"])
            self.assertEqual(client_info["lib-ver"], self.lib.__version__)
        else:
            # Redis versions below 7.2 lack CLIENT SETINFO.
            self.assertNotIn("lib-ver", client_info)
            self.assertNotIn("lib-name", client_info)