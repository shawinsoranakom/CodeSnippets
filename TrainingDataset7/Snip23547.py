def test_assign_content_object_in_init(self):
        spinach = Vegetable(name="spinach")
        tag = TaggedItem(content_object=spinach)
        self.assertEqual(tag.content_object, spinach)