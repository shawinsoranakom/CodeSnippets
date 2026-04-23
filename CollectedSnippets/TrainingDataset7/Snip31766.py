def test_altering_serialized_output(self):
        """
        The ability to create new objects by modifying serialized content.
        """
        old_headline = "Poker has no place on ESPN"
        new_headline = "Poker has no place on television"
        serial_str = serializers.serialize(self.serializer_name, Article.objects.all())
        serial_str = serial_str.replace(old_headline, new_headline)
        models = list(serializers.deserialize(self.serializer_name, serial_str))

        # Prior to saving, old headline is in place
        self.assertTrue(Article.objects.filter(headline=old_headline))
        self.assertFalse(Article.objects.filter(headline=new_headline))

        for model in models:
            model.save()

        # After saving, new headline is in place
        self.assertTrue(Article.objects.filter(headline=new_headline))
        self.assertFalse(Article.objects.filter(headline=old_headline))