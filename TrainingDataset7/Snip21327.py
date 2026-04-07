def setUp(self):
        self.company_query = Company.objects.values(
            "name", "num_employees", "num_chairs"
        ).order_by("name", "num_employees", "num_chairs")