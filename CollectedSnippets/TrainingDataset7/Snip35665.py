def test_update_fields_only_2(self):
        s = Person.objects.create(name="Sara", gender="F", pid=22)
        self.assertEqual(s.gender, "F")

        s1 = Person.objects.only("name").get(pk=s.pk)
        s1.name = "Emily"
        s1.gender = "M"

        with self.assertNumQueries(2):
            s1.save(update_fields=["pid"])

        s2 = Person.objects.get(pk=s1.pk)
        self.assertEqual(s2.name, "Sara")
        self.assertEqual(s2.gender, "F")