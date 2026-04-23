def test_pk_attributes(self):
        """
        pk and attribute name are available on the model
        No default id attribute is added
        """
        # pk can be used as a substitute for the primary key.
        # The primary key can be accessed via the pk property on the model.
        e = Employee.objects.get(pk=123)
        self.assertEqual(e.pk, 123)
        # Or we can use the real attribute name for the primary key:
        self.assertEqual(e.employee_code, 123)

        with self.assertRaisesMessage(
            AttributeError, "'Employee' object has no attribute 'id'"
        ):
            e.id