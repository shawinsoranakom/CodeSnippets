def test_related_objects_have_name_attribute(self):
        for field_name in ("test_issue_client", "test_issue_cc"):
            obj = User._meta.get_field(field_name)
            self.assertEqual(field_name, obj.field.related_query_name())