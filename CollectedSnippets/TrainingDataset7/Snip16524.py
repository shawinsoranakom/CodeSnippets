def test_changelist_view(self):
        response = self.client.get(reverse("admin:admin_views_emptymodel_changelist"))
        for i in self.pks:
            if i > 1:
                self.assertContains(response, "Primary key = %s" % i)
            else:
                self.assertNotContains(response, "Primary key = %s" % i)