def test_access_via_content_type(self):
        """
        Test lookups through content type.
        """
        self.lion.delete()
        self.platypus.tags.create(tag="fatty")

        ctype = ContentType.objects.get_for_model(self.platypus)

        self.assertSequenceEqual(
            Animal.objects.filter(tags__content_type=ctype),
            [self.platypus],
        )