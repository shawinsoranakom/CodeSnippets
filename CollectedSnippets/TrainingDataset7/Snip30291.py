def test_basic_proxy(self):
        """
        Creating a Person makes them accessible through the MyPerson proxy.
        """
        person = Person.objects.create(name="Foo McBar")
        self.assertEqual(len(Person.objects.all()), 1)
        self.assertEqual(len(MyPerson.objects.all()), 1)
        self.assertEqual(MyPerson.objects.get(name="Foo McBar").id, person.id)
        self.assertFalse(MyPerson.objects.get(id=person.id).has_special_name())