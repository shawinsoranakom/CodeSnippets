def test_clear_input_checked_returns_false_only_if_not_required(self):
        """
        ClearableFileInput.value_from_datadict never returns False if the field
        is required.
        """
        widget = ClearableFileInput()
        widget.is_required = True
        field = SimpleUploadedFile("something.txt", b"content")

        value = widget.value_from_datadict(
            data={"myfile-clear": True},
            files={"myfile": field},
            name="myfile",
        )
        self.assertEqual(value, field)
        self.assertIs(widget.checked, True)