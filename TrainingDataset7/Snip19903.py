def test_only_not_clear_cached_private_relations(self):
        obj = Answer.objects.only("content_type", "object_id").get(pk=self.answer.pk)
        with self.assertNumQueries(1):
            obj.question
        obj.text  # Accessing a deferred field.
        with self.assertNumQueries(0):
            obj.question