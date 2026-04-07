def test_get_get_or_create(self):
        tag = Tag.objects.create(text="foo")
        a_thing = Thing.objects.create(name="a")
        a_thing.tags.add(tag)
        obj, created = a_thing.tags.get_or_create(text="foo")

        self.assertFalse(created)
        self.assertEqual(obj.pk, tag.pk)