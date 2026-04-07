def test_post_submission(self):
        data = {
            "form-TOTAL_FORMS": "3",
            "form-INITIAL_FORMS": "3",
            "form-MAX_NUM_FORMS": "0",
            "form-0-gender": "1",
            "form-0-id": str(self.per1.pk),
            "form-1-gender": "2",
            "form-1-id": str(self.per2.pk),
            "form-2-alive": "checked",
            "form-2-gender": "1",
            "form-2-id": str(self.per3.pk),
            "_save": "Save",
        }
        self.client.post(reverse("admin:admin_views_person_changelist"), data)

        self.assertIs(Person.objects.get(name="John Mauchly").alive, False)
        self.assertEqual(Person.objects.get(name="Grace Hopper").gender, 2)

        # test a filtered page
        data = {
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "2",
            "form-MAX_NUM_FORMS": "0",
            "form-0-id": str(self.per1.pk),
            "form-0-gender": "1",
            "form-0-alive": "checked",
            "form-1-id": str(self.per3.pk),
            "form-1-gender": "1",
            "form-1-alive": "checked",
            "_save": "Save",
        }
        self.client.post(
            reverse("admin:admin_views_person_changelist") + "?gender__exact=1", data
        )

        self.assertIs(Person.objects.get(name="John Mauchly").alive, True)

        # test a searched page
        data = {
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "1",
            "form-MAX_NUM_FORMS": "0",
            "form-0-id": str(self.per1.pk),
            "form-0-gender": "1",
            "_save": "Save",
        }
        self.client.post(
            reverse("admin:admin_views_person_changelist") + "?q=john", data
        )

        self.assertIs(Person.objects.get(name="John Mauchly").alive, False)