def test_defer(self):
        self.PersonModel.objects.create(name="Joe", mugshot=self.file1)
        with self.assertNumQueries(1):
            qs = list(self.PersonModel.objects.defer("mugshot"))
        with self.assertNumQueries(0):
            self.assertEqual(qs[0].name, "Joe")