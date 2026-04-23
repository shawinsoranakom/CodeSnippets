def test_file_field_data(self):
        # Test conditions when files is either not given or empty.
        f = TextFileForm(data={"description": "Assistance"})
        self.assertFalse(f.is_valid())
        f = TextFileForm(data={"description": "Assistance"}, files={})
        self.assertFalse(f.is_valid())

        # Upload a file and ensure it all works as expected.
        f = TextFileForm(
            data={"description": "Assistance"},
            files={"file": SimpleUploadedFile("test1.txt", b"hello world")},
        )
        self.assertTrue(f.is_valid())
        self.assertEqual(type(f.cleaned_data["file"]), SimpleUploadedFile)
        instance = f.save()
        self.assertEqual(instance.file.name, "tests/test1.txt")
        instance.file.delete()

        # If the previous file has been deleted, the file name can be reused
        f = TextFileForm(
            data={"description": "Assistance"},
            files={"file": SimpleUploadedFile("test1.txt", b"hello world")},
        )
        self.assertTrue(f.is_valid())
        self.assertEqual(type(f.cleaned_data["file"]), SimpleUploadedFile)
        instance = f.save()
        self.assertEqual(instance.file.name, "tests/test1.txt")

        # Check if the max_length attribute has been inherited from the model.
        f = TextFileForm(
            data={"description": "Assistance"},
            files={"file": SimpleUploadedFile("test-maxlength.txt", b"hello world")},
        )
        self.assertFalse(f.is_valid())

        # Edit an instance that already has the file defined in the model. This
        # will not save the file again, but leave it exactly as it is.
        f = TextFileForm({"description": "Assistance"}, instance=instance)
        self.assertTrue(f.is_valid())
        self.assertEqual(f.cleaned_data["file"].name, "tests/test1.txt")
        instance = f.save()
        self.assertEqual(instance.file.name, "tests/test1.txt")

        # Delete the current file since this is not done by Django.
        instance.file.delete()

        # Override the file by uploading a new one.
        f = TextFileForm(
            data={"description": "Assistance"},
            files={"file": SimpleUploadedFile("test2.txt", b"hello world")},
            instance=instance,
        )
        self.assertTrue(f.is_valid())
        instance = f.save()
        self.assertEqual(instance.file.name, "tests/test2.txt")

        # Delete the current file since this is not done by Django.
        instance.file.delete()
        instance.delete()