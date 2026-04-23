def test_needs_multipart_true(self):
        """
        needs_multipart_form should be True if any widgets need it.
        """
        widget = MyMultiWidget(widgets=(TextInput(), FileInput()))
        self.assertTrue(widget.needs_multipart_form)