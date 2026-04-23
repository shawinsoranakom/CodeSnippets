def test_select_related_preserved(self):
        """
        Regression test for #10348: ChangeList.get_queryset() shouldn't
        overwrite a custom select_related provided by
        ModelAdmin.get_queryset().
        """
        m = ChildAdmin(Child, custom_site)
        request = self.factory.get("/child/")
        request.user = self.superuser
        cl = m.get_changelist_instance(request)
        self.assertEqual(cl.queryset.query.select_related, {"parent": {}})