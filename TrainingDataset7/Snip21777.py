def test_foreign_key_db_default(self):
        parent1 = DBDefaultsPK.objects.create(language_code="fr")
        child1 = DBDefaultsFK.objects.create()
        if not connection.features.can_return_columns_from_insert:
            child1.refresh_from_db()
        self.assertEqual(child1.language_code, parent1)

        parent2 = DBDefaultsPK.objects.create()
        if not connection.features.can_return_columns_from_insert:
            # refresh_from_db() cannot be used because that needs the pk to
            # already be known to Django.
            parent2 = DBDefaultsPK.objects.get(pk="en")
        child2 = DBDefaultsFK.objects.create(language_code=parent2)
        self.assertEqual(child2.language_code, parent2)