def test_printing_field_error(self):
        field = SimpleModel._meta.get_field("field")
        e = Error("Error", obj=field)
        expected = "check_framework.SimpleModel.field: Error"
        self.assertEqual(str(e), expected)