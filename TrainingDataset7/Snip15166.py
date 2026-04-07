def test_get_edited_object_ids(self):
        a = Swallow.objects.create(origin="Swallow A", load=4, speed=1)
        b = Swallow.objects.create(origin="Swallow B", load=2, speed=2)
        c = Swallow.objects.create(origin="Swallow C", load=5, speed=5)
        superuser = self._create_superuser("superuser")
        self.client.force_login(superuser)
        changelist_url = reverse("admin:admin_changelist_swallow_changelist")
        m = SwallowAdmin(Swallow, custom_site)
        data = {
            "form-TOTAL_FORMS": "3",
            "form-INITIAL_FORMS": "3",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-uuid": str(a.pk),
            "form-1-uuid": str(b.pk),
            "form-2-uuid": str(c.pk),
            "form-0-load": "9.0",
            "form-0-speed": "9.0",
            "form-1-load": "5.0",
            "form-1-speed": "5.0",
            "form-2-load": "5.0",
            "form-2-speed": "4.0",
            "_save": "Save",
        }
        request = self.factory.post(changelist_url, data=data)
        pks = m._get_edited_object_pks(request, prefix="form")
        self.assertEqual(sorted(pks), sorted([str(a.pk), str(b.pk), str(c.pk)]))