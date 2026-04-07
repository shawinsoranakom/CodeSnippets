def test_access_content_object(self):
        """
        Test accessing the content object like a foreign key.
        """
        tagged_item = TaggedItem.objects.get(tag="salty")
        self.assertEqual(tagged_item.content_object, self.bacon)