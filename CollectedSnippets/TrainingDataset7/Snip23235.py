def test_clear_input_checked_returns_false(self):
        """
        ClearableFileInput.value_from_datadict returns False if the clear
        checkbox is checked, if not required.
        """
        value = self.widget.value_from_datadict(
            data={"myfile-clear": True},
            files={},
            name="myfile",
        )
        self.assertIs(value, False)
        self.assertIs(self.widget.checked, True)