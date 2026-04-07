def test_issue_7853(self):
        """
        Regression test for #7853
        If the parent class has a self-referential link, make sure that any
        updates to that link via the child update the right table.
        """
        obj = SelfRefChild.objects.create(child_data=37, parent_data=42)
        obj.delete()