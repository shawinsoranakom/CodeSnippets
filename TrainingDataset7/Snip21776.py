def test_pk_db_default(self):
        obj1 = DBDefaultsPK.objects.create()
        if not connection.features.can_return_columns_from_insert:
            # refresh_from_db() cannot be used because that needs the pk to
            # already be known to Django.
            obj1 = DBDefaultsPK.objects.get(pk="en")
        self.assertEqual(obj1.pk, "en")
        self.assertEqual(obj1.language_code, "en")

        obj2 = DBDefaultsPK.objects.create(language_code="de")
        self.assertEqual(obj2.pk, "de")
        self.assertEqual(obj2.language_code, "de")