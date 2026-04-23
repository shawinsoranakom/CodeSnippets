def test_order_of_operations(self):
        # Law of order of operations is followed
        self.company_query.update(
            num_chairs=F("num_employees") + 2 * F("num_employees")
        )
        self.assertSequenceEqual(
            self.company_query,
            [
                {"num_chairs": 6900, "name": "Example Inc.", "num_employees": 2300},
                {"num_chairs": 9, "name": "Foobar Ltd.", "num_employees": 3},
                {"num_chairs": 96, "name": "Test GmbH", "num_employees": 32},
            ],
        )