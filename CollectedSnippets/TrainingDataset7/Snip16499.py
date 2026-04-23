def test_list_editable_action_choices(self):
        # List editable changes should be executed if the "Save" button is
        # used to submit the form - any action choices should be ignored.
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
            "_selected_action": ["1"],
            "action": ["", "delete_selected"],
        }
        self.client.post(reverse("admin:admin_views_person_changelist"), data)

        self.assertIs(Person.objects.get(name="John Mauchly").alive, False)
        self.assertEqual(Person.objects.get(name="Grace Hopper").gender, 2)