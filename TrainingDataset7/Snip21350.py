def test_parenthesis_priority(self):
        # Law of order of operations can be overridden by parentheses
        self.company_query.update(
            num_chairs=(F("num_employees") + 2) * F("num_employees")
        )
        self.assertSequenceEqual(
            self.company_query,
            [
                {"num_chairs": 5294600, "name": "Example Inc.", "num_employees": 2300},
                {"num_chairs": 15, "name": "Foobar Ltd.", "num_employees": 3},
                {"num_chairs": 1088, "name": "Test GmbH", "num_employees": 32},
            ],
        )