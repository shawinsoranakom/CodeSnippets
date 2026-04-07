def test_update_fields_only_repeated(self):
        s = Person.objects.create(name="Sara", gender="F")
        self.assertEqual(s.gender, "F")

        s1 = Person.objects.only("name").get(pk=s.pk)
        s1.gender = "M"
        with self.assertNumQueries(1):
            s1.save()
        # save() should not fetch deferred fields
        s1 = Person.objects.only("name").get(pk=s.pk)
        with self.assertNumQueries(1):
            s1.save()