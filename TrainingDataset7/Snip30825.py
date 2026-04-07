def test_col_not_in_list_containing_null(self):
        self.assertQuerySetEqual(
            NullableName.objects.exclude(name__in=[None]), ["i1"], attrgetter("name")
        )