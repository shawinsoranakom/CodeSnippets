def test_upload_to_callable_sees_auto_now_add_field_value(self):
        d = DocumentWithTimestamp(myfile=ContentFile(b"content", name="foo"))
        d.save()
        self.assertIsNotNone(d.created_at)
        self.assertIs(d.myfile.name.startswith(f"{d.created_at.year}/foo"), True)