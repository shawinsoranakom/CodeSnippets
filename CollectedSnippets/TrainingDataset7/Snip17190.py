def test_chained_values_masked_annotation_error_message(self):
        msg = (
            "Cannot select the 'author_id' alias. It was excluded by a "
            "previous values() or values_list() call. Include 'author_id' in "
            "that call to select it."
        )
        with self.assertRaisesMessage(FieldError, msg):
            Book.objects.annotate(
                author_name=F("authors__name"), author_id=F("authors__id")
            ).values("author_name").values("author_id")