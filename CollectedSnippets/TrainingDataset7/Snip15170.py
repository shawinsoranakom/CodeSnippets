def test_list_editable_error_title(self):
        a = Swallow.objects.create(origin="Swallow A", load=4, speed=1)
        Swallow.objects.create(origin="Swallow B", load=2, speed=2)
        data = {
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "2",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-uuid": str(a.pk),
            "form-0-load": "invalid",
            "_save": "Save",
        }
        superuser = self._create_superuser("superuser")
        self.client.force_login(superuser)
        changelist_url = reverse("admin:admin_changelist_swallow_changelist")
        response = self.client.post(changelist_url, data=data)
        self.assertContains(response, "Error: Select swallow to change")