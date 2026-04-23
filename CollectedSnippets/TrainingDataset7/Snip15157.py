def test_show_all(self):
        parent = Parent.objects.create(name="anything")
        for i in range(1, 31):
            Child.objects.create(name="name %s" % i, parent=parent)
            Child.objects.create(name="filtered %s" % i, parent=parent)

        # Add "show all" parameter to request
        request = self.factory.get("/child/", data={ALL_VAR: ""})
        request.user = self.superuser

        # Test valid "show all" request (number of total objects is under max)
        m = ChildAdmin(Child, custom_site)
        m.list_max_show_all = 200
        # 200 is the max we'll pass to ChangeList
        cl = m.get_changelist_instance(request)
        cl.get_results(request)
        self.assertEqual(len(cl.result_list), 60)

        # Test invalid "show all" request (number of total objects over max)
        # falls back to paginated pages
        m = ChildAdmin(Child, custom_site)
        m.list_max_show_all = 30
        # 30 is the max we'll pass to ChangeList for this test
        cl = m.get_changelist_instance(request)
        cl.get_results(request)
        self.assertEqual(len(cl.result_list), 10)