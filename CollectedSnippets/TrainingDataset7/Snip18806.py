def test_django_date_extract(self):
        """
        Test the custom ``django_date_extract method``, in particular against
        fields which clash with strings passed to it (e.g. 'day') (#12818).
        """
        updated = datetime.datetime(2010, 2, 20)
        SchoolClass.objects.create(year=2009, last_updated=updated)
        classes = SchoolClass.objects.filter(last_updated__day=20)
        self.assertEqual(len(classes), 1)