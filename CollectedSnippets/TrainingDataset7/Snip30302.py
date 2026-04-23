def test_otherperson_manager(self):
        Person.objects.create(name="fred")
        Person.objects.create(name="wilma")
        Person.objects.create(name="barney")

        resp = [p.name for p in OtherPerson.objects.all()]
        self.assertEqual(resp, ["barney", "wilma"])

        resp = [p.name for p in OtherPerson.excluder.all()]
        self.assertEqual(resp, ["barney", "fred"])

        resp = [p.name for p in OtherPerson._default_manager.all()]
        self.assertEqual(resp, ["barney", "wilma"])