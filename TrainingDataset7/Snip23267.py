def test_value_from_datadict_multiple(self):
        class MultipleFileInput(FileInput):
            allow_multiple_selected = True

        file_1 = SimpleUploadedFile("something1.txt", b"content 1")
        file_2 = SimpleUploadedFile("something2.txt", b"content 2")
        # Uploading multiple files is allowed.
        widget = MultipleFileInput(attrs={"multiple": True})
        value = widget.value_from_datadict(
            data={"name": "Test name"},
            files=MultiValueDict({"myfile": [file_1, file_2]}),
            name="myfile",
        )
        self.assertEqual(value, [file_1, file_2])
        # Uploading multiple files is not allowed.
        widget = FileInput()
        value = widget.value_from_datadict(
            data={"name": "Test name"},
            files=MultiValueDict({"myfile": [file_1, file_2]}),
            name="myfile",
        )
        self.assertEqual(value, file_2)