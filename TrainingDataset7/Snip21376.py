def test_lookups_subquery(self):
        smallest_company = Company.objects.order_by("num_employees").values("name")[:1]
        for lookup in CharField.get_lookups():
            if lookup == "isnull":
                continue  # not allowed, rhs must be a literal boolean.
            if (
                lookup == "in"
                and not connection.features.allow_sliced_subqueries_with_in
            ):
                continue
            if lookup == "range":
                rhs = (Subquery(smallest_company), Subquery(smallest_company))
            else:
                rhs = Subquery(smallest_company)
            with self.subTest(lookup=lookup):
                qs = Company.objects.filter(**{f"name__{lookup}": rhs})
                self.assertGreater(len(qs), 0)