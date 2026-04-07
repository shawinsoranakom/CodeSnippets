def test_create_inlines_on_inherited_model(self):
        """
        An object can be created with inlines when it inherits another class.
        """
        data = {
            "name": "Martian",
            "sighting_set-TOTAL_FORMS": 1,
            "sighting_set-INITIAL_FORMS": 0,
            "sighting_set-MAX_NUM_FORMS": 0,
            "sighting_set-0-place": "Zone 51",
            "_save": "Save",
        }
        response = self.client.post(
            reverse("admin:admin_inlines_extraterrestrial_add"), data
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Sighting.objects.filter(et__name="Martian").count(), 1)