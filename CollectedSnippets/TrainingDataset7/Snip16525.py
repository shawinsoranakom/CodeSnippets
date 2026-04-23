def test_changelist_view_count_queries(self):
        # create 2 Person objects
        Person.objects.create(name="person1", gender=1)
        Person.objects.create(name="person2", gender=2)
        changelist_url = reverse("admin:admin_views_person_changelist")

        # 5 queries are expected: 1 for the session, 1 for the user,
        # 2 for the counts and 1 for the objects on the page
        with self.assertNumQueries(5):
            resp = self.client.get(changelist_url)
            self.assertEqual(resp.context["selection_note"], "0 of 2 selected")
            self.assertEqual(resp.context["selection_note_all"], "All 2 selected")
        with self.assertNumQueries(5):
            extra = {"q": "not_in_name"}
            resp = self.client.get(changelist_url, extra)
            self.assertEqual(resp.context["selection_note"], "0 of 0 selected")
            self.assertEqual(resp.context["selection_note_all"], "All 0 selected")
        with self.assertNumQueries(5):
            extra = {"q": "person"}
            resp = self.client.get(changelist_url, extra)
            self.assertEqual(resp.context["selection_note"], "0 of 2 selected")
            self.assertEqual(resp.context["selection_note_all"], "All 2 selected")
        with self.assertNumQueries(5):
            extra = {"gender__exact": "1"}
            resp = self.client.get(changelist_url, extra)
            self.assertEqual(resp.context["selection_note"], "0 of 1 selected")
            self.assertEqual(resp.context["selection_note_all"], "1 selected")