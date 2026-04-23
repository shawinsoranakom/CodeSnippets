def test_update(self):
        # We can set one field to have the value of another field
        # Make sure we have enough chairs
        self.company_query.update(num_chairs=F("num_employees"))
        self.assertSequenceEqual(
            self.company_query,
            [
                {"num_chairs": 2300, "name": "Example Inc.", "num_employees": 2300},
                {"num_chairs": 3, "name": "Foobar Ltd.", "num_employees": 3},
                {"num_chairs": 32, "name": "Test GmbH", "num_employees": 32},
            ],
        )