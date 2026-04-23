def test_deepcopy(self):
        """
        __deepcopy__() should copy all attributes properly.
        """
        widget = self.widget()
        obj = copy.deepcopy(widget)
        self.assertIsNot(widget, obj)
        self.assertEqual(widget.choices, obj.choices)
        self.assertIsNot(widget.choices, obj.choices)
        self.assertEqual(widget.attrs, obj.attrs)
        self.assertIsNot(widget.attrs, obj.attrs)