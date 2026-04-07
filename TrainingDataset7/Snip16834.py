def test_label_and_url_for_value_invalid_uuid(self):
        field = Bee._meta.get_field("honeycomb")
        self.assertIsInstance(field.target_field, UUIDField)
        widget = widgets.ForeignKeyRawIdWidget(field.remote_field, admin.site)
        self.assertEqual(widget.label_and_url_for_value("invalid-uuid"), ("", ""))