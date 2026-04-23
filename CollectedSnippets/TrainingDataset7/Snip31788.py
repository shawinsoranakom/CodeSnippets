def test_forward_refs(self):
        """
        Objects ids can be referenced before they are
        defined in the serialization data.
        """
        # The deserialization process needs to run in a transaction in order
        # to test forward reference handling.
        with transaction.atomic():
            objs = serializers.deserialize(self.serializer_name, self.fwd_ref_str)
            with connection.constraint_checks_disabled():
                for obj in objs:
                    obj.save()

        for model_cls in (Category, Author, Article):
            self.assertEqual(model_cls.objects.count(), 1)
        art_obj = Article.objects.all()[0]
        self.assertEqual(art_obj.categories.count(), 1)
        self.assertEqual(art_obj.author.name, "Agnes")