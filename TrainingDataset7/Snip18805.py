def test_django_date_trunc(self):
        """
        Test the custom ``django_date_trunc method``, in particular against
        fields which clash with strings passed to it (e.g. 'year') (#12818).
        """
        updated = datetime.datetime(2010, 2, 20)
        SchoolClass.objects.create(year=2009, last_updated=updated)
        years = SchoolClass.objects.dates("last_updated", "year")
        self.assertEqual(list(years), [datetime.date(2010, 1, 1)])