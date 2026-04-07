def test_related_gte_lookup(self):
        """
        Regression test for #10153: foreign key __gte lookups.
        """
        Worker.objects.filter(department__gte=0)