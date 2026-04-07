def test_list_editable_action_submit(self):
        # List editable changes should not be executed if the action "Go"
        # button is used to submit the form.
        data = {
            "form-TOTAL_FORMS": "3",
            "form-INITIAL_FORMS": "3",
            "form-MAX_NUM_FORMS": "0",
            "form-0-gender": "1",
            "form-0-id": "1",
            "form-1-gender": "2",
            "form-1-id": "2",
            "form-2-alive": "checked",
            "form-2-gender": "1",
            "form-2-id": "3",
            "index": "0",
            "_selected_action": ["3"],
            "action": ["", "delete_selected"],
        }
        self.client.post(reverse("admin:admin_views_person_changelist"), data)

        self.assertIs(Person.objects.get(name="John Mauchly").alive, True)
        self.assertEqual(Person.objects.get(name="Grace Hopper").gender, 1)