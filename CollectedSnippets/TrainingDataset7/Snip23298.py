def test_needs_multipart_false(self):
        """
        needs_multipart_form should be False if no widgets need it.
        """
        widget = MyMultiWidget(widgets=(TextInput(), TextInput()))
        self.assertFalse(widget.needs_multipart_form)