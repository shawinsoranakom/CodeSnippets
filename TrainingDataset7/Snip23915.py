def test_create_get_or_create(self):
        a_thing = Thing.objects.create(name="a")
        obj, created = a_thing.tags.get_or_create(text="foo")

        self.assertTrue(created)
        self.assertEqual(obj.text, "foo")
        self.assertIn(obj, a_thing.tags.all())