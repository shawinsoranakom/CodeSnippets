def test_validate_constraints_with_foreign_object(self):
        customer_tab = CustomerTab(customer_id=1500)
        with self.assertRaisesMessage(ValidationError, "customer_id_limit"):
            customer_tab.validate_constraints()