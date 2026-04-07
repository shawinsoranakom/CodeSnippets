def test_filefield_required_false(self):
        # Test the non-required FileField
        f = TextFileForm(data={"description": "Assistance"})
        f.fields["file"].required = False
        self.assertTrue(f.is_valid())
        instance = f.save()
        self.assertEqual(instance.file.name, "")

        f = TextFileForm(
            data={"description": "Assistance"},
            files={"file": SimpleUploadedFile("test3.txt", b"hello world")},
            instance=instance,
        )
        self.assertTrue(f.is_valid())
        instance = f.save()
        self.assertEqual(instance.file.name, "tests/test3.txt")

        # Instance can be edited w/out re-uploading the file and existing file
        # should be preserved.
        f = TextFileForm({"description": "New Description"}, instance=instance)
        f.fields["file"].required = False
        self.assertTrue(f.is_valid())
        instance = f.save()
        self.assertEqual(instance.description, "New Description")
        self.assertEqual(instance.file.name, "tests/test3.txt")

        # Delete the current file since this is not done by Django.
        instance.file.delete()
        instance.delete()