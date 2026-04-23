def test_update_fields_deferred(self):
        s = Person.objects.create(name="Sara", gender="F", pid=22)
        self.assertEqual(s.gender, "F")

        s1 = Person.objects.defer("gender", "pid").get(pk=s.pk)
        s1.name = "Emily"
        s1.gender = "M"

        with self.assertNumQueries(1):
            s1.save()

        s2 = Person.objects.get(pk=s1.pk)
        self.assertEqual(s2.name, "Emily")
        self.assertEqual(s2.gender, "M")