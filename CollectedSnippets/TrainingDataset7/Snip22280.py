def test_natural_key_dependencies(self):
        """
        Natural keys with foreign keys in dependencies works in a multiple
        database setup.
        """
        management.call_command(
            "loaddata",
            "nk_with_foreign_key.json",
            database="other",
            verbosity=0,
        )
        obj = NaturalKeyWithFKDependency.objects.using("other").get()
        self.assertEqual(obj.name, "The Lord of the Rings")
        self.assertEqual(obj.author.name, "J.R.R. Tolkien")