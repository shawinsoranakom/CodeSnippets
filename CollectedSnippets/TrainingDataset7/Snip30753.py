def test_named_values_list_bad_field_name(self):
        msg = "Type names and field names must be valid identifiers: '1'"
        with self.assertRaisesMessage(ValueError, msg):
            Number.objects.extra(select={"1": "num+1"}).values_list(
                "1", named=True
            ).first()