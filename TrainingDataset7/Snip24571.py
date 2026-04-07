def test05_select_related_fk_to_subclass(self):
        """
        select_related on a query over a model with an FK to a model subclass.
        """
        # Regression test for #9752.
        list(DirectoryEntry.objects.select_related())