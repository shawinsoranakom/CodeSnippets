def test_update_inherited_field_value(self):
        msg = "Joined field references are not permitted in this query"
        with self.assertRaisesMessage(FieldError, msg):
            RemoteEmployee.objects.update(adjusted_salary=F("salary") * 5)