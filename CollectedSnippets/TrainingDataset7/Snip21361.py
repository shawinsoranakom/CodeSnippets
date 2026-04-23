def test_object_update_unsaved_objects(self):
        # F expressions cannot be used to update attributes on objects which do
        # not yet exist in the database
        acme = Company(
            name="The Acme Widget Co.", num_employees=12, num_chairs=5, ceo=self.max
        )
        acme.num_employees = F("num_employees") + 16
        msg = (
            'Failed to insert expression "Col(expressions_company, '
            'expressions.Company.num_employees) + Value(16)" on '
            "expressions.Company.num_employees. F() expressions can only be "
            "used to update, not to insert."
        )
        with self.assertRaisesMessage(ValueError, msg):
            acme.save()

        acme.num_employees = 12
        acme.name = Lower(F("name"))
        msg = (
            'Failed to insert expression "Lower(Col(expressions_company, '
            'expressions.Company.name))" on expressions.Company.name. F() '
            "expressions can only be used to update, not to insert."
        )
        with self.assertRaisesMessage(ValueError, msg):
            acme.save()