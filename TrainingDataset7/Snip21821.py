def test_filefield_awss3_storage(self):
        """
        Simulate a FileField with an S3 storage which uses keys rather than
        folders and names. FileField and Storage shouldn't have any os.path()
        calls that break the key.
        """
        storage = AWSS3Storage()
        folder = "not/a/folder/"

        f = FileField(upload_to=folder, storage=storage)
        key = "my-file-key\\with odd characters"
        data = ContentFile("test")
        expected_key = AWSS3Storage.prefix + folder + key

        # Simulate call to f.save()
        result_key = f.generate_filename(None, key)
        self.assertEqual(result_key, expected_key)

        result_key = storage.save(result_key, data)
        self.assertEqual(result_key, expected_key)

        # Repeat test with a callable.
        def upload_to(instance, filename):
            # Return a non-normalized path on purpose.
            return folder + filename

        f = FileField(upload_to=upload_to, storage=storage)

        # Simulate call to f.save()
        result_key = f.generate_filename(None, key)
        self.assertEqual(result_key, expected_key)

        result_key = storage.save(result_key, data)
        self.assertEqual(result_key, expected_key)