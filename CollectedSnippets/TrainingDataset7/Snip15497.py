def test_inline_primary(self):
        person = Person.objects.create(firstname="Imelda")
        item = OutfitItem.objects.create(name="Shoes")
        # Imelda likes shoes, but can't carry her own bags.
        data = {
            "shoppingweakness_set-TOTAL_FORMS": 1,
            "shoppingweakness_set-INITIAL_FORMS": 0,
            "shoppingweakness_set-MAX_NUM_FORMS": 0,
            "_save": "Save",
            "person": person.id,
            "max_weight": 0,
            "shoppingweakness_set-0-item": item.id,
        }
        response = self.client.post(
            reverse("admin:admin_inlines_fashionista_add"), data
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(Fashionista.objects.filter(person__firstname="Imelda")), 1)