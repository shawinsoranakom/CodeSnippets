def test_model_name_not_available_in_queryset_lookup(self):
        msg = "Cannot resolve keyword 'book' into field."
        with self.assertRaisesMessage(FieldError, msg):
            Author.objects.get(book=self.book)