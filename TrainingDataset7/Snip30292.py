def test_no_proxy(self):
        """
        Person is not proxied by StatusPerson subclass.
        """
        Person.objects.create(name="Foo McBar")
        self.assertEqual(list(StatusPerson.objects.all()), [])