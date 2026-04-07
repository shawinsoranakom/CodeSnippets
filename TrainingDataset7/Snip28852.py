def test_related_lte_lookup(self):
        """
        Regression test for #10153: foreign key __lte lookups.
        """
        Worker.objects.filter(department__lte=0)