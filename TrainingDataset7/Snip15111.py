def test_repr(self):
        m = ChildAdmin(Child, custom_site)
        request = self.factory.get("/child/")
        request.user = self.superuser
        cl = m.get_changelist_instance(request)
        self.assertEqual(repr(cl), "<ChangeList: model=Child model_admin=ChildAdmin>")