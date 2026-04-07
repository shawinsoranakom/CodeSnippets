def test_name(self):
        """
        Tests the outputting of the correct name if assigned one.
        """
        # First try using a "normal" field
        field = models.CharField(max_length=65)
        name, path, args, kwargs = field.deconstruct()
        self.assertIsNone(name)
        field.set_attributes_from_name("is_awesome_test")
        name, path, args, kwargs = field.deconstruct()
        self.assertEqual(name, "is_awesome_test")
        # Now try with a ForeignKey
        field = models.ForeignKey("some_fake.ModelName", models.CASCADE)
        name, path, args, kwargs = field.deconstruct()
        self.assertIsNone(name)
        field.set_attributes_from_name("author")
        name, path, args, kwargs = field.deconstruct()
        self.assertEqual(name, "author")