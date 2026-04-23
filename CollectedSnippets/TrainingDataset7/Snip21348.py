def test_arithmetic(self):
        # We can perform arithmetic operations in expressions
        # Make sure we have 2 spare chairs
        self.company_query.update(num_chairs=F("num_employees") + 2)
        self.assertSequenceEqual(
            self.company_query,
            [
                {"num_chairs": 2302, "name": "Example Inc.", "num_employees": 2300},
                {"num_chairs": 5, "name": "Foobar Ltd.", "num_employees": 3},
                {"num_chairs": 34, "name": "Test GmbH", "num_employees": 32},
            ],
        )