def test_something(self):
        Tag.objects.create(text="foo")
        a_thing = Thing.objects.create(name="a")
        with self.assertRaises(IntegrityError):
            a_thing.tags.get_or_create(text="foo")