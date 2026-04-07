def test_setting_changed(self):
        """
        Properties using settings values as defaults should be updated on
        referenced settings change while specified values should be unchanged.
        """
        storage = InMemoryStorage(
            location="explicit_location",
            base_url="explicit_base_url/",
            file_permissions_mode=0o666,
            directory_permissions_mode=0o666,
        )
        defaults_storage = InMemoryStorage()
        settings = {
            "MEDIA_ROOT": "overridden_media_root",
            "MEDIA_URL": "/overridden_media_url/",
            "FILE_UPLOAD_PERMISSIONS": 0o333,
            "FILE_UPLOAD_DIRECTORY_PERMISSIONS": 0o333,
        }
        with self.settings(**settings):
            self.assertEqual(storage.base_location, "explicit_location")
            self.assertIn("explicit_location", storage.location)
            self.assertEqual(storage.base_url, "explicit_base_url/")
            self.assertEqual(storage.file_permissions_mode, 0o666)
            self.assertEqual(storage.directory_permissions_mode, 0o666)
            self.assertEqual(defaults_storage.base_location, settings["MEDIA_ROOT"])
            self.assertIn(settings["MEDIA_ROOT"], defaults_storage.location)
            self.assertEqual(defaults_storage.base_url, settings["MEDIA_URL"])
            self.assertEqual(
                defaults_storage.file_permissions_mode,
                settings["FILE_UPLOAD_PERMISSIONS"],
            )
            self.assertEqual(
                defaults_storage.directory_permissions_mode,
                settings["FILE_UPLOAD_DIRECTORY_PERMISSIONS"],
            )