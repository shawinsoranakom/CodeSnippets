def test_mti_update_non_local_concrete_fields(self):
        journalist = Journalist.objects.create(name="Jane", specialty="Politics")
        journalist, created = Journalist.objects.update_or_create(
            pk=journalist.pk,
            defaults={"name": "John"},
        )
        self.assertIs(created, False)
        self.assertEqual(journalist.name, "John")