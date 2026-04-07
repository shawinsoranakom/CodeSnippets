def test_filter_inter_attribute(self):
        # We can filter on attribute relationships on same model obj, e.g.
        # find companies where the number of employees is greater
        # than the number of chairs.
        self.assertSequenceEqual(
            self.company_query.filter(num_employees__gt=F("num_chairs")),
            [
                {
                    "num_chairs": 5,
                    "name": "Example Inc.",
                    "num_employees": 2300,
                },
                {"num_chairs": 1, "name": "Test GmbH", "num_employees": 32},
            ],
        )