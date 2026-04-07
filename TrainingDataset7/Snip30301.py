def test_myperson_manager(self):
        Person.objects.create(name="fred")
        Person.objects.create(name="wilma")
        Person.objects.create(name="barney")

        resp = [p.name for p in MyPerson.objects.all()]
        self.assertEqual(resp, ["barney", "fred"])

        resp = [p.name for p in MyPerson._default_manager.all()]
        self.assertEqual(resp, ["barney", "fred"])