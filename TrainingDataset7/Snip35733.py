def test_non_identifier_parameter_name_causes_exception(self):
        msg = (
            "URL route 'b/<int:book.id>/' uses parameter name 'book.id' which "
            "isn't a valid Python identifier."
        )
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            path(r"b/<int:book.id>/", lambda r: None)