def test_validate_constraints_excluding_foreign_object(self):
        customer_tab = CustomerTab(customer_id=150)
        customer_tab.validate_constraints(exclude={"customer"})